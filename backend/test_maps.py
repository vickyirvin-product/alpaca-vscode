"""Tests for Google Maps integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response
from backend.services.maps_service import MapsService
from backend.models.maps import PlaceSuggestion, PlaceDetails


@pytest.fixture
def maps_service():
    """Create a maps service instance for testing."""
    return MapsService()


@pytest.fixture
def mock_autocomplete_response():
    """Mock Google Places Autocomplete API response."""
    return {
        "status": "OK",
        "predictions": [
            {
                "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
                "description": "New York, NY, USA",
                "structured_formatting": {
                    "main_text": "New York",
                    "secondary_text": "NY, USA"
                }
            },
            {
                "place_id": "ChIJ-RuN5V4EdkgRRjXFXy_RP6E",
                "description": "New York, UK",
                "structured_formatting": {
                    "main_text": "New York",
                    "secondary_text": "UK"
                }
            }
        ]
    }


@pytest.fixture
def mock_place_details_response():
    """Mock Google Places Details API response."""
    return {
        "status": "OK",
        "result": {
            "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
            "name": "New York",
            "formatted_address": "New York, NY, USA",
            "geometry": {
                "location": {
                    "lat": 40.7127753,
                    "lng": -74.0059728
                }
            },
            "types": ["locality", "political"]
        }
    }


class TestMapsServiceAutocomplete:
    """Tests for destination autocomplete functionality."""
    
    @pytest.mark.asyncio
    async def test_autocomplete_success(self, maps_service, mock_autocomplete_response):
        """Test successful autocomplete request."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = mock_autocomplete_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            results = await maps_service.autocomplete_destination("New York")
            
            assert len(results) == 2
            assert results[0]["place_id"] == "ChIJOwg_06VPwokRYv534QaPC8g"
            assert results[0]["description"] == "New York, NY, USA"
            assert results[0]["main_text"] == "New York"
            assert results[0]["secondary_text"] == "NY, USA"
    
    @pytest.mark.asyncio
    async def test_autocomplete_empty_query(self, maps_service):
        """Test autocomplete with empty query."""
        results = await maps_service.autocomplete_destination("")
        assert results == []
        
        results = await maps_service.autocomplete_destination("  ")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_autocomplete_short_query(self, maps_service):
        """Test autocomplete with query less than 2 characters."""
        results = await maps_service.autocomplete_destination("N")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_autocomplete_zero_results(self, maps_service):
        """Test autocomplete with no results."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = {
                "status": "ZERO_RESULTS",
                "predictions": []
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            results = await maps_service.autocomplete_destination("XYZ123456")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_autocomplete_api_error(self, maps_service):
        """Test autocomplete with API error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = {
                "status": "REQUEST_DENIED",
                "error_message": "Invalid API key"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await maps_service.autocomplete_destination("Paris")
            
            assert "REQUEST_DENIED" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_autocomplete_network_error(self, maps_service):
        """Test autocomplete with network error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception) as exc_info:
                await maps_service.autocomplete_destination("London")
            
            assert "Network error" in str(exc_info.value)


class TestMapsServicePlaceDetails:
    """Tests for place details functionality."""
    
    @pytest.mark.asyncio
    async def test_place_details_success(self, maps_service, mock_place_details_response):
        """Test successful place details request."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = mock_place_details_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = await maps_service.get_place_details("ChIJOwg_06VPwokRYv534QaPC8g")
            
            assert result is not None
            assert result["place_id"] == "ChIJOwg_06VPwokRYv534QaPC8g"
            assert result["name"] == "New York"
            assert result["formatted_address"] == "New York, NY, USA"
            assert result["lat"] == 40.7127753
            assert result["lng"] == -74.0059728
            assert "locality" in result["types"]
    
    @pytest.mark.asyncio
    async def test_place_details_empty_place_id(self, maps_service):
        """Test place details with empty place_id."""
        result = await maps_service.get_place_details("")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_place_details_not_found(self, maps_service):
        """Test place details with invalid place_id."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = {
                "status": "NOT_FOUND"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = await maps_service.get_place_details("invalid_place_id")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_place_details_api_error(self, maps_service):
        """Test place details with API error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock(spec=Response)
            mock_response.json.return_value = {
                "status": "INVALID_REQUEST",
                "error_message": "Invalid request"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await maps_service.get_place_details("ChIJOwg_06VPwokRYv534QaPC8g")
            
            assert "INVALID_REQUEST" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_place_details_network_error(self, maps_service):
        """Test place details with network error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")
            
            with pytest.raises(Exception) as exc_info:
                await maps_service.get_place_details("ChIJOwg_06VPwokRYv534QaPC8g")
            
            assert "Connection timeout" in str(exc_info.value)


class TestMapsModels:
    """Tests for maps Pydantic models."""
    
    def test_place_suggestion_model(self):
        """Test PlaceSuggestion model validation."""
        suggestion = PlaceSuggestion(
            place_id="ChIJOwg_06VPwokRYv534QaPC8g",
            description="New York, NY, USA",
            main_text="New York",
            secondary_text="NY, USA"
        )
        
        assert suggestion.place_id == "ChIJOwg_06VPwokRYv534QaPC8g"
        assert suggestion.description == "New York, NY, USA"
        assert suggestion.main_text == "New York"
        assert suggestion.secondary_text == "NY, USA"
    
    def test_place_details_model(self):
        """Test PlaceDetails model validation."""
        details = PlaceDetails(
            place_id="ChIJOwg_06VPwokRYv534QaPC8g",
            name="New York",
            formatted_address="New York, NY, USA",
            lat=40.7127753,
            lng=-74.0059728,
            types=["locality", "political"]
        )
        
        assert details.place_id == "ChIJOwg_06VPwokRYv534QaPC8g"
        assert details.name == "New York"
        assert details.lat == 40.7127753
        assert details.lng == -74.0059728
        assert len(details.types) == 2
    
    def test_place_details_model_defaults(self):
        """Test PlaceDetails model with default values."""
        details = PlaceDetails(
            place_id="test_id",
            name="Test Place",
            formatted_address="Test Address",
            lat=0.0,
            lng=0.0
        )
        
        assert details.types == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])