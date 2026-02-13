import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from models.trip import TripCreate
from models.trip_generation_job import TripGenerationJobResponse, JobStats
from routes.auth import get_current_user
from services.trip_generation_job_service import trip_generation_job_service
from services.trip_generation_service import trip_generation_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trip-generation", tags=["trip-generation"])


@router.post(
    "/jobs",
    response_model=TripGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_trip_generation_job(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
):
    job = await trip_generation_job_service.create_job(
        user_id=current_user.id,
        trip_data=trip_data.model_dump(),
    )

    # Start background job processing with timeout wrapper
    asyncio.create_task(process_trip_generation_job_with_timeout(job.id))

    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=TripGenerationJobResponse)
async def get_trip_generation_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    job = await trip_generation_job_service.get_job(job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_response(job)


@router.get("/jobs/stats", response_model=JobStats)
async def get_job_stats(current_user: User = Depends(get_current_user)):
    """Get statistics about trip generation jobs."""
    return await trip_generation_job_service.get_job_stats()


@router.get("/jobs/health")
async def get_jobs_health(current_user: User = Depends(get_current_user)):
    """Health check endpoint that reports on stuck jobs."""
    stuck_jobs = await trip_generation_job_service.get_stuck_jobs()
    stats = await trip_generation_job_service.get_job_stats()
    
    is_healthy = len(stuck_jobs) == 0 and stats.processing < 10
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "stuck_jobs_count": len(stuck_jobs),
        "processing_jobs_count": stats.processing,
        "timestamp": datetime.utcnow().isoformat()
    }


async def process_trip_generation_job_with_timeout(job_id: str) -> None:
    """Wrapper that enforces timeout and handles retries."""
    try:
        await asyncio.wait_for(
            process_trip_generation_job(job_id),
            timeout=settings.trip_generation_timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.error(
            f"Job {job_id} timed out after {settings.trip_generation_timeout_seconds}s",
            extra={"job_id": job_id, "timeout_seconds": settings.trip_generation_timeout_seconds}
        )
        
        # Check if we should retry
        should_retry = await trip_generation_job_service.should_retry(job_id)
        
        if should_retry:
            await trip_generation_job_service.increment_retry(job_id)
            # Calculate exponential backoff: 2^retry_count seconds
            job = await trip_generation_job_service.get_job(job_id)
            if job:
                backoff_seconds = 2 ** job.retry_count
                logger.info(f"Retrying job {job_id} after {backoff_seconds}s backoff")
                await asyncio.sleep(backoff_seconds)
                asyncio.create_task(process_trip_generation_job_with_timeout(job_id))
        else:
            await trip_generation_job_service.mark_failed(
                job_id,
                error_message=f"Job timed out after {settings.trip_generation_timeout_seconds} seconds",
                error_type="timeout"
            )
    except Exception as err:
        logger.error(
            f"Unexpected error in job timeout wrapper for {job_id}: {err}",
            extra={"job_id": job_id, "error": str(err)}
        )


async def process_trip_generation_job(job_id: str) -> None:
    job = await trip_generation_job_service.get_job(job_id)
    if not job:
        return

    try:
        await trip_generation_job_service.mark_processing(job_id)
        
        # Log warning if job takes too long
        warning_task = asyncio.create_task(
            _log_slow_job_warning(job_id, settings.trip_generation_warning_threshold_seconds)
        )
        
        trip_create = TripCreate(**job.trip_data)
        trip = await trip_generation_service.generate_trip(
            user_id=job.user_id,
            trip_data=trip_create,
        )
        
        # Cancel warning task if job completes
        warning_task.cancel()
        
        await trip_generation_job_service.mark_completed(job_id, trip_id=trip.id)
        logger.info(
            f"Job {job_id} completed successfully",
            extra={"job_id": job_id, "trip_id": trip.id, "user_id": job.user_id}
        )
        
    except ValueError as err:
        # Validation errors should not be retried
        error_msg = f"Validation error: {str(err)}"
        logger.warning(
            f"Job {job_id} failed validation",
            extra={"job_id": job_id, "error": error_msg}
        )
        await trip_generation_job_service.mark_failed(
            job_id,
            error_message=error_msg,
            error_type="validation"
        )
        
    except Exception as err:
        error_msg = str(err)
        error_type = _classify_error(err)
        
        logger.error(
            f"Job {job_id} failed with {error_type} error",
            extra={"job_id": job_id, "error_type": error_type, "error": error_msg}
        )
        
        # Check if we should retry transient errors
        if error_type == "transient":
            should_retry = await trip_generation_job_service.should_retry(job_id)
            if should_retry:
                await trip_generation_job_service.increment_retry(job_id)
                job = await trip_generation_job_service.get_job(job_id)
                if job:
                    backoff_seconds = 2 ** job.retry_count
                    logger.info(f"Retrying job {job_id} after {backoff_seconds}s backoff")
                    await asyncio.sleep(backoff_seconds)
                    asyncio.create_task(process_trip_generation_job_with_timeout(job_id))
                return
        
        await trip_generation_job_service.mark_failed(
            job_id,
            error_message=error_msg,
            error_type=error_type
        )


async def _log_slow_job_warning(job_id: str, threshold_seconds: int) -> None:
    """Log a warning if job takes longer than threshold."""
    try:
        await asyncio.sleep(threshold_seconds)
        logger.warning(
            f"Job {job_id} is taking longer than {threshold_seconds}s",
            extra={"job_id": job_id, "threshold_seconds": threshold_seconds}
        )
    except asyncio.CancelledError:
        pass


def _classify_error(error: Exception) -> str:
    """Classify error type for retry logic."""
    error_str = str(error).lower()
    
    # Transient errors that should be retried
    if any(keyword in error_str for keyword in ["timeout", "connection", "network", "temporary"]):
        return "transient"
    
    # API errors (may or may not be transient)
    if any(keyword in error_str for keyword in ["api", "rate limit", "quota"]):
        return "api_error"
    
    # Validation errors should not be retried
    if any(keyword in error_str for keyword in ["validation", "invalid", "required"]):
        return "validation"
    
    return "unknown"


def _job_to_response(job) -> TripGenerationJobResponse:
    return TripGenerationJobResponse(
        jobId=job.id,
        status=job.status,
        tripId=job.trip_id,
        error=job.error_message,
        errorType=job.error_type,
        retryCount=job.retry_count,
        createdAt=job.created_at,
        updatedAt=job.updated_at,
    )


# Background task for periodic cleanup
async def cleanup_old_jobs_task():
    """Periodic task to cleanup old jobs."""
    while True:
        try:
            await asyncio.sleep(settings.job_cleanup_interval_seconds)
            deleted_count = await trip_generation_job_service.cleanup_old_jobs()
            if deleted_count > 0:
                logger.info(f"Cleanup task deleted {deleted_count} old jobs")
        except Exception as err:
            logger.error(f"Error in cleanup task: {err}")