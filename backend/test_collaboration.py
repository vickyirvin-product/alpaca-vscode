"""Tests for collaboration features (nudges and trip sharing)."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from bson import ObjectId

from .main import app
from .database import get_db
from .models.trip import TripInDB, TravelerInDB, NudgeInDB
from .models.user import UserInDB


@pytest.fixture
async def test_user():
    """Create a test user."""
    db = get_db()
    users_collection = db.users
    
    user = UserInDB(
        id=str(ObjectId()),
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.utcnow()
    )
    
    await users_collection.insert_one(user.model_dump())
    yield user
    
    # Cleanup
    await users_collection.delete_one({"id": user.id})


@pytest.fixture
async def test_user2():
    """Create a second test user."""
    db = get_db()
    users_collection = db.users
    
    user = UserInDB(
        id=str(ObjectId()),
        email="emma.smith@example.com",
        full_name="Emma Smith",
        created_at=datetime.utcnow()
    )
    
    await users_collection.insert_one(user.model_dump())
    yield user
    
    # Cleanup
    await users_collection.delete_one({"id": user.id})


@pytest.fixture
async def test_trip(test_user):
    """Create a test trip."""
    db = get_db()
    trips_collection = db.trips
    
    travelers = [
        TravelerInDB(
            id=str(ObjectId()),
            name="Emma Smith",
            age=8,
            type="child",
            avatar=None
        ),
        TravelerInDB(
            id=str(ObjectId()),
            name="Lucas Brown",
            age=10,
            type="child",
            avatar=None
        )
    ]
    
    trip = TripInDB(
        id=str(ObjectId()),
        user_id=test_user.id,
        destination="Paris",
        start_date="2024-07-01",
        end_date="2024-07-10",
        activities=["sightseeing", "museums"],
        transport=["plane"],
        travelers=travelers,
        packing_lists=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await trips_collection.insert_one(trip.model_dump())
    yield trip
    
    # Cleanup
    await trips_collection.delete_one({"id": trip.id})


@pytest.fixture
async def auth_headers(test_user):
    """Create authentication headers for test user."""
    from .auth.security import create_access_token
    
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def auth_headers2(test_user2):
    """Create authentication headers for second test user."""
    from .auth.security import create_access_token
    
    access_token = create_access_token(data={"sub": test_user2.email})
    return {"Authorization": f"Bearer {access_token}"}


class TestNudges:
    """Test nudge functionality."""
    
    @pytest.mark.asyncio
    async def test_send_nudge_to_existing_user(self, test_trip, test_user, test_user2, auth_headers):
        """Test sending a nudge to a user with an account."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Get the first traveler (Emma Smith)
            person_id = test_trip.travelers[0].id
            
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Don't forget to pack your favorite toys!"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["trip_id"] == test_trip.id
            assert data["from_user_id"] == test_user.id
            assert data["to_user_email"] == "emma.smith@example.com"
            assert data["message"] == "Don't forget to pack your favorite toys!"
            assert data["is_read"] is False
            assert data["trip_destination"] == "Paris"
            assert "id" in data
    
    @pytest.mark.asyncio
    async def test_send_nudge_to_non_user(self, test_trip, test_user, auth_headers):
        """Test sending a nudge to someone without an account."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Get the second traveler (Lucas Brown - no account)
            person_id = test_trip.travelers[1].id
            
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Time to start packing!"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["to_user_email"] == "lucas.brown@example.com"
            assert data["message"] == "Time to start packing!"
    
    @pytest.mark.asyncio
    async def test_send_nudge_invalid_trip(self, auth_headers):
        """Test sending a nudge for a non-existent trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/trips/invalid_trip_id/nudges",
                json={
                    "person_id": "person123",
                    "message": "Test"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_send_nudge_invalid_person(self, test_trip, auth_headers):
        """Test sending a nudge to a person not in the trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": "invalid_person_id",
                    "message": "Test"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 404
            assert "Person not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_nudges(self, test_trip, test_user, test_user2, auth_headers, auth_headers2):
        """Test retrieving nudges for a user."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send a nudge first
            person_id = test_trip.travelers[0].id
            await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Pack your bags!"
                },
                headers=auth_headers
            )
            
            # Get nudges for Emma (test_user2)
            response = await client.get(
                "/api/v1/nudges",
                headers=auth_headers2
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert data[0]["to_user_email"] == test_user2.email
            assert data[0]["is_read"] is False
    
    @pytest.mark.asyncio
    async def test_get_unread_nudges_only(self, test_trip, test_user, test_user2, auth_headers, auth_headers2):
        """Test retrieving only unread nudges."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send a nudge
            person_id = test_trip.travelers[0].id
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Test nudge"
                },
                headers=auth_headers
            )
            nudge_id = response.json()["id"]
            
            # Mark as read
            await client.put(
                f"/api/v1/nudges/{nudge_id}/mark-read",
                headers=auth_headers2
            )
            
            # Get unread nudges only
            response = await client.get(
                "/api/v1/nudges?unread_only=true",
                headers=auth_headers2
            )
            
            assert response.status_code == 200
            data = response.json()
            # Should not include the read nudge
            assert all(nudge["is_read"] is False for nudge in data)
    
    @pytest.mark.asyncio
    async def test_mark_nudge_as_read(self, test_trip, test_user, test_user2, auth_headers, auth_headers2):
        """Test marking a nudge as read."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send a nudge
            person_id = test_trip.travelers[0].id
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Test nudge"
                },
                headers=auth_headers
            )
            nudge_id = response.json()["id"]
            
            # Mark as read
            response = await client.put(
                f"/api/v1/nudges/{nudge_id}/mark-read",
                headers=auth_headers2
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_read"] is True
            assert data["id"] == nudge_id
    
    @pytest.mark.asyncio
    async def test_mark_nudge_unauthorized(self, test_trip, test_user, auth_headers):
        """Test marking someone else's nudge as read."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to mark a non-existent nudge
            response = await client.put(
                "/api/v1/nudges/invalid_nudge_id/mark-read",
                headers=auth_headers
            )
            
            assert response.status_code == 404


class TestTripSharing:
    """Test trip sharing functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_share_link(self, test_trip, auth_headers):
        """Test generating a share link for a trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={"expiration_days": 7},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "share_url" in data
            assert "share_token" in data
            assert "expires_at" in data
            assert data["share_token"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_share_link_no_expiration(self, test_trip, auth_headers):
        """Test generating a share link without expiration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["expires_at"] is None
    
    @pytest.mark.asyncio
    async def test_generate_share_link_unauthorized(self, test_trip, auth_headers2):
        """Test generating a share link for someone else's trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={},
                headers=auth_headers2
            )
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_access_shared_trip(self, test_trip, auth_headers):
        """Test accessing a trip via share token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Generate share link
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={},
                headers=auth_headers
            )
            share_token = response.json()["share_token"]
            
            # Access shared trip (no auth required)
            response = await client.get(
                f"/api/v1/trips/shared/{share_token}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_trip.id
            assert data["destination"] == "Paris"
    
    @pytest.mark.asyncio
    async def test_access_shared_trip_invalid_token(self):
        """Test accessing a trip with invalid share token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/trips/shared/invalid_token"
            )
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_access_expired_share_link(self, test_trip, auth_headers):
        """Test accessing a trip with expired share link."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Generate share link with 0 days expiration (already expired)
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={"expiration_days": 0},
                headers=auth_headers
            )
            share_token = response.json()["share_token"]
            
            # Manually set expiration to past
            db = get_db()
            trips_collection = db.trips
            await trips_collection.update_one(
                {"id": test_trip.id},
                {"$set": {"share_expires_at": datetime.utcnow() - timedelta(days=1)}}
            )
            
            # Try to access
            response = await client.get(
                f"/api/v1/trips/shared/{share_token}"
            )
            
            assert response.status_code == 410
            assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_revoke_share_link(self, test_trip, auth_headers):
        """Test revoking a share link."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Generate share link
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={},
                headers=auth_headers
            )
            share_token = response.json()["share_token"]
            
            # Revoke share link
            response = await client.delete(
                f"/api/v1/trips/{test_trip.id}/share",
                headers=auth_headers
            )
            
            assert response.status_code == 204
            
            # Try to access revoked link
            response = await client.get(
                f"/api/v1/trips/shared/{share_token}"
            )
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_revoke_share_link_unauthorized(self, test_trip, auth_headers2):
        """Test revoking someone else's share link."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/trips/{test_trip.id}/share",
                headers=auth_headers2
            )
            
            assert response.status_code == 404


class TestCollaborationIntegration:
    """Integration tests for collaboration features."""
    
    @pytest.mark.asyncio
    async def test_full_nudge_workflow(self, test_trip, test_user, test_user2, auth_headers, auth_headers2):
        """Test complete nudge workflow from send to read."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Send nudge
            person_id = test_trip.travelers[0].id
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/nudges",
                json={
                    "person_id": person_id,
                    "message": "Complete workflow test"
                },
                headers=auth_headers
            )
            assert response.status_code == 201
            nudge_id = response.json()["id"]
            
            # 2. Recipient checks nudges
            response = await client.get(
                "/api/v1/nudges",
                headers=auth_headers2
            )
            assert response.status_code == 200
            nudges = response.json()
            assert any(n["id"] == nudge_id for n in nudges)
            
            # 3. Recipient marks as read
            response = await client.put(
                f"/api/v1/nudges/{nudge_id}/mark-read",
                headers=auth_headers2
            )
            assert response.status_code == 200
            assert response.json()["is_read"] is True
    
    @pytest.mark.asyncio
    async def test_full_sharing_workflow(self, test_trip, auth_headers):
        """Test complete sharing workflow from generate to revoke."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Generate share link
            response = await client.post(
                f"/api/v1/trips/{test_trip.id}/share",
                json={"expiration_days": 30},
                headers=auth_headers
            )
            assert response.status_code == 200
            share_token = response.json()["share_token"]
            
            # 2. Access shared trip
            response = await client.get(
                f"/api/v1/trips/shared/{share_token}"
            )
            assert response.status_code == 200
            assert response.json()["id"] == test_trip.id
            
            # 3. Revoke access
            response = await client.delete(
                f"/api/v1/trips/{test_trip.id}/share",
                headers=auth_headers
            )
            assert response.status_code == 204
            
            # 4. Verify access is revoked
            response = await client.get(
                f"/api/v1/trips/shared/{share_token}"
            )
            assert response.status_code == 404