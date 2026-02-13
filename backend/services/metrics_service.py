from datetime import datetime
from typing import Any, Dict, Optional

from database import get_db


class MetricsService:
    """Service for recording operational metrics to MongoDB."""

    COLLECTION_NAME = "trip_generation_metrics"

    async def record_trip_generation_metric(
        self,
        *,
        user_id: str,
        status: str,
        timings_ms: Dict[str, int],
        metadata: Dict[str, Any],
        trip_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Persist a trip generation metric document.

        Args:
            user_id: Authenticated user initiating the generation.
            status: 'success' | 'failed'.
            timings_ms: Dict of timing measurements (e.g., weather_ms, llm_ms).
            metadata: Additional contextual data (destination, traveler_count, etc.).
            trip_id: Generated trip ID when available.
            error_message: Optional error summary if status == failed.
        """
        db = get_db()
        collection = db[self.COLLECTION_NAME]

        metric_doc = {
            "user_id": user_id,
            "trip_id": trip_id,
            "status": status,
            "timings_ms": timings_ms,
            "metadata": metadata,
            "error_message": error_message,
            "created_at": datetime.utcnow(),
        }

        await collection.insert_one(metric_doc)


metrics_service = MetricsService()