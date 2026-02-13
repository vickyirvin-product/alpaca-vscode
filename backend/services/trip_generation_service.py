from datetime import datetime
from time import perf_counter
from typing import Dict, Optional, List

from bson import ObjectId

from database import get_db
from models.trip import TripCreate, TripInDB, TravelerInDB, WeatherInfo
from services.avatar_service import avatar_service
from services.llm_service import llm_service
from services.metrics_service import metrics_service
from services.weather_service import weather_service


# List of US states and territories for transport inference
US_LOCATIONS = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "puerto rico", "guam",
    "us virgin islands", "american samoa", "northern mariana islands",
    "united states", "usa", "u.s.", "u.s.a."
]


class TripGenerationService:
    """Encapsulates trip generation workflow and metrics recording."""

    def _infer_transport(self, destination: str, transport: List[str]) -> List[str]:
        """
        Infer transport method based on destination if not provided.
        
        Args:
            destination: Trip destination
            transport: User-provided transport (may be empty)
            
        Returns:
            Inferred or provided transport list
        """
        # If transport is already provided and not empty, use it
        if transport and len(transport) > 0:
            return transport
        
        # Check if destination is in the US
        destination_lower = destination.lower()
        is_us_destination = any(loc in destination_lower for loc in US_LOCATIONS)
        
        if is_us_destination:
            # US destination - set to unknown/let LLM decide
            return ["unknown"]
        else:
            # International destination - assume flying
            return ["flying"]

    async def generate_trip(self, *, user_id: str, trip_data: TripCreate) -> TripInDB:
        """
        Generate a trip, persist it, and record timing metrics.

        Args:
            user_id: Owner of the trip.
            trip_data: Trip creation payload.

        Returns:
            TripInDB: The persisted trip document.

        Raises:
            Exception: Propagates any failure so callers can handle HTTP responses.
        """
        db = get_db()
        trips_collection = db.trips

        metrics_metadata: Dict[str, Optional[str | list[str] | int]] = {
            "destination": trip_data.destination,
            "activities": trip_data.activities,
            "transport": trip_data.transport,
            "traveler_count": len(trip_data.travelers),
        }
        timings_ms: Dict[str, int] = {}
        weather_data: Optional[WeatherInfo] = None
        total_start = perf_counter()
        
        # Infer transport if not provided
        inferred_transport = self._infer_transport(trip_data.destination, trip_data.transport)

        try:
            # Step 1: Weather fetch (with timeout fallback handled in service)
            weather_start = perf_counter()
            try:
                weather_info = await weather_service.get_forecast(
                    location=trip_data.destination,
                    start_date=trip_data.start_date,
                    end_date=trip_data.end_date,
                )
                weather_data = WeatherInfo(**weather_info)
            except Exception as weather_err:
                weather_data = None
                print(f"Weather fetch failed: {weather_err}")
            finally:
                timings_ms["weather_fetch_ms"] = int(
                    (perf_counter() - weather_start) * 1000
                )

            # Step 2: Traveler preparation (avatars etc.)
            traveler_start = perf_counter()
            travelers_db: list[TravelerInDB] = []
            for traveler in trip_data.travelers:
                avatar = traveler.avatar
                if not avatar:
                    avatar = avatar_service.assign_avatar(
                        {
                            "age": traveler.age,
                            "gender": getattr(traveler, "gender", None),
                            "type": traveler.type,
                        }
                    )

                travelers_db.append(
                    TravelerInDB(
                        id=str(ObjectId()),
                        name=traveler.name,
                        age=traveler.age,
                        type=traveler.type,
                        avatar=avatar,
                    )
                )
            timings_ms["traveler_prep_ms"] = int(
                (perf_counter() - traveler_start) * 1000
            )

            # Step 3: LLM generation
            llm_start = perf_counter()
            packing_lists = await llm_service.generate_packing_lists(
                destination=trip_data.destination,
                start_date=trip_data.start_date,
                end_date=trip_data.end_date,
                travelers=travelers_db,
                weather_data=weather_data,
                activities=trip_data.activities,
                transport=inferred_transport,  # Use inferred transport
            )
            timings_ms["llm_generation_ms"] = int(
                (perf_counter() - llm_start) * 1000
            )

            # Step 4: Persist trip
            trip = TripInDB(
                id=str(ObjectId()),
                user_id=user_id,
                destination=trip_data.destination,
                start_date=trip_data.start_date,
                end_date=trip_data.end_date,
                activities=trip_data.activities,
                transport=inferred_transport,  # Use inferred transport
                travelers=travelers_db,
                weather_data=weather_data,
                packing_lists=packing_lists,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            trip_dict = trip.model_dump()
            trip_dict["created_at"] = trip.created_at
            trip_dict["updated_at"] = trip.updated_at
            await trips_collection.insert_one(trip_dict)

            # Step 5: Metrics (success)
            timings_ms["total_ms"] = int((perf_counter() - total_start) * 1000)
            await metrics_service.record_trip_generation_metric(
                user_id=user_id,
                status="success",
                timings_ms=timings_ms,
                metadata={**metrics_metadata, "weather_included": weather_data is not None},
                trip_id=trip.id,
            )

            return trip

        except Exception as err:
            timings_ms.setdefault("total_ms", int((perf_counter() - total_start) * 1000))
            try:
                await metrics_service.record_trip_generation_metric(
                    user_id=user_id,
                    status="failed",
                    timings_ms=timings_ms,
                    metadata={
                        **metrics_metadata,
                        "weather_included": weather_data is not None,
                    },
                    trip_id=None,
                    error_message=str(err),
                )
            except Exception:
                # Avoid masking original exception if metrics logging fails
                pass
            raise err


trip_generation_service = TripGenerationService()