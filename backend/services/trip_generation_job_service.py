from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Literal
import logging

from database import get_db
from models.trip_generation_job import TripGenerationJob, JobStats
from config import settings

logger = logging.getLogger(__name__)


class TripGenerationJobService:
    """Persistence helpers for trip generation background jobs."""

    COLLECTION_NAME = "trip_generation_jobs"

    async def create_job(self, *, user_id: str, trip_data: Dict[str, Any]) -> TripGenerationJob:
        """Create a pending trip generation job."""
        job = TripGenerationJob(user_id=user_id, trip_data=trip_data)
        await self._collection.insert_one(job.model_dump())
        return job

    async def mark_processing(self, job_id: str) -> None:
        """Mark a job as processing and record start time."""
        await self._update_job(job_id, {
            "status": "processing",
            "started_at": datetime.utcnow()
        })

    async def mark_completed(self, job_id: str, *, trip_id: str) -> None:
        """Mark job completed and attach generated trip ID."""
        await self._update_job(job_id, {
            "status": "completed",
            "trip_id": trip_id,
            "completed_at": datetime.utcnow()
        })

    async def mark_failed(
        self,
        job_id: str,
        *,
        error_message: str,
        error_type: Literal["timeout", "validation", "api_error", "transient", "unknown"] = "unknown"
    ) -> None:
        """Mark job failed with error context."""
        await self._update_job(job_id, {
            "status": "failed",
            "error_message": error_message,
            "error_type": error_type,
            "completed_at": datetime.utcnow()
        })
        logger.error(
            f"Job {job_id} failed",
            extra={
                "job_id": job_id,
                "error_type": error_type,
                "error_message": error_message
            }
        )

    async def get_job(self, job_id: str) -> Optional[TripGenerationJob]:
        """Fetch a job by ID."""
        doc = await self._collection.find_one({"id": job_id})
        return TripGenerationJob(**doc) if doc else None

    async def should_retry(self, job_id: str) -> bool:
        """Check if a job should be retried based on retry count and error type."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        # Don't retry validation errors or if max retries exceeded
        if job.error_type == "validation":
            return False
        
        return job.retry_count < job.max_retries

    async def increment_retry(self, job_id: str) -> None:
        """Increment retry count and reset status to pending."""
        job = await self.get_job(job_id)
        if not job:
            return
        
        retry_count = job.retry_count + 1
        await self._update_job(job_id, {
            "status": "pending",
            "retry_count": retry_count,
            "started_at": None,
            "error_message": None,
            "error_type": None
        })
        logger.info(
            f"Job {job_id} queued for retry {retry_count}/{job.max_retries}",
            extra={"job_id": job_id, "retry_count": retry_count}
        )

    async def cleanup_old_jobs(self) -> int:
        """Delete jobs older than configured max age. Returns count of deleted jobs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=settings.job_max_age_hours)
        result = await self._collection.delete_many({
            "created_at": {"$lt": cutoff_time},
            "status": {"$in": ["completed", "failed"]}
        })
        deleted_count = result.deleted_count
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old jobs")
        return deleted_count

    async def get_stuck_jobs(self) -> list[TripGenerationJob]:
        """Find jobs that have been processing for too long."""
        cutoff_time = datetime.utcnow() - timedelta(
            seconds=settings.trip_generation_timeout_seconds
        )
        cursor = self._collection.find({
            "status": "processing",
            "started_at": {"$lt": cutoff_time}
        })
        docs = await cursor.to_list(length=100)
        return [TripGenerationJob(**doc) for doc in docs]

    async def get_job_stats(self) -> JobStats:
        """Get statistics about job statuses."""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        
        stats = JobStats()
        for result in results:
            status = result["_id"]
            count = result["count"]
            if status == "pending":
                stats.pending = count
            elif status == "processing":
                stats.processing = count
            elif status == "completed":
                stats.completed = count
            elif status == "failed":
                stats.failed = count
            stats.total += count
        
        # Count stuck jobs
        stuck_jobs = await self.get_stuck_jobs()
        stats.stuck = len(stuck_jobs)
        
        return stats

    async def _update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        updates["updated_at"] = datetime.utcnow()
        await self._collection.update_one({"id": job_id}, {"$set": updates})

    @property
    def _collection(self):
        db = get_db()
        return db[self.COLLECTION_NAME]


trip_generation_job_service = TripGenerationJobService()