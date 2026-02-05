"""Tests for smart avatar assignment logic."""
import pytest
from backend.services.avatar_service import AvatarService


@pytest.fixture
def avatar_service():
    """Create an avatar service instance for testing."""
    return AvatarService()


class TestAvatarAssignmentInfants:
    """Tests for infant avatar assignment (0-2 years)."""
    
    def test_infant_age_0(self, avatar_service):
        """Test avatar for 0-year-old infant."""
        traveler = {"age": 0, "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_infant_age_1(self, avatar_service):
        """Test avatar for 1-year-old infant."""
        traveler = {"age": 1, "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_infant_age_2(self, avatar_service):
        """Test avatar for 2-year-old infant."""
        traveler = {"age": 2, "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_infant_with_gender_male(self, avatar_service):
        """Test that infant avatar is gender-neutral even with male gender."""
        traveler = {"age": 1, "gender": "male", "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_infant_with_gender_female(self, avatar_service):
        """Test that infant avatar is gender-neutral even with female gender."""
        traveler = {"age": 1, "gender": "female", "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_infant_type_overrides_age(self, avatar_service):
        """Test that infant type overrides age for avatar selection."""
        traveler = {"age": 5, "type": "infant"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"


class TestAvatarAssignmentChildren:
    """Tests for child avatar assignment (3-12 years)."""
    
    def test_child_age_3_female(self, avatar_service):
        """Test avatar for 3-year-old female child."""
        traveler = {"age": 3, "gender": "female", "type": "child"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👧"
    
    def test_child_age_3_male(self, avatar_service):
        """Test avatar for 3-year-old male child."""
        traveler = {"age": 3, "gender": "male", "type": "child"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👦"
    
    def test_child_age_7_female(self, avatar_service):
        """Test avatar for 7-year-old female child."""
        traveler = {"age": 7, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👧"
    
    def test_child_age_7_male(self, avatar_service):
        """Test avatar for 7-year-old male child."""
        traveler = {"age": 7, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👦"
    
    def test_child_age_12_female(self, avatar_service):
        """Test avatar for 12-year-old female child."""
        traveler = {"age": 12, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👧"
    
    def test_child_age_12_male(self, avatar_service):
        """Test avatar for 12-year-old male child."""
        traveler = {"age": 12, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👦"
    
    def test_child_no_gender(self, avatar_service):
        """Test avatar for child with no gender specified."""
        traveler = {"age": 8}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "🧑"
    
    def test_child_type_overrides_age(self, avatar_service):
        """Test that child type overrides age for avatar selection."""
        traveler = {"age": 15, "gender": "female", "type": "child"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👧"


class TestAvatarAssignmentTeens:
    """Tests for teen avatar assignment (13-17 years)."""
    
    def test_teen_age_13_female(self, avatar_service):
        """Test avatar for 13-year-old female teen."""
        traveler = {"age": 13, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_teen_age_13_male(self, avatar_service):
        """Test avatar for 13-year-old male teen."""
        traveler = {"age": 13, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_teen_age_15_female(self, avatar_service):
        """Test avatar for 15-year-old female teen."""
        traveler = {"age": 15, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_teen_age_15_male(self, avatar_service):
        """Test avatar for 15-year-old male teen."""
        traveler = {"age": 15, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_teen_age_17_female(self, avatar_service):
        """Test avatar for 17-year-old female teen."""
        traveler = {"age": 17, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_teen_age_17_male(self, avatar_service):
        """Test avatar for 17-year-old male teen."""
        traveler = {"age": 17, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_teen_no_gender(self, avatar_service):
        """Test avatar for teen with no gender specified."""
        traveler = {"age": 15}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "🧑"


class TestAvatarAssignmentAdults:
    """Tests for adult avatar assignment (18+ years)."""
    
    def test_adult_age_18_female(self, avatar_service):
        """Test avatar for 18-year-old female adult."""
        traveler = {"age": 18, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_adult_age_18_male(self, avatar_service):
        """Test avatar for 18-year-old male adult."""
        traveler = {"age": 18, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_adult_age_30_female(self, avatar_service):
        """Test avatar for 30-year-old female adult."""
        traveler = {"age": 30, "gender": "female", "type": "adult"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_adult_age_30_male(self, avatar_service):
        """Test avatar for 30-year-old male adult."""
        traveler = {"age": 30, "gender": "male", "type": "adult"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_adult_age_65_female(self, avatar_service):
        """Test avatar for 65-year-old female adult."""
        traveler = {"age": 65, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"
    
    def test_adult_age_65_male(self, avatar_service):
        """Test avatar for 65-year-old male adult."""
        traveler = {"age": 65, "gender": "male"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"
    
    def test_adult_no_gender(self, avatar_service):
        """Test avatar for adult with no gender specified."""
        traveler = {"age": 25}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "🧑"
    
    def test_adult_type_overrides_age(self, avatar_service):
        """Test that adult type overrides age for avatar selection."""
        traveler = {"age": 10, "gender": "male", "type": "adult"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👨"


class TestAvatarAssignmentEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_empty_traveler_dict(self, avatar_service):
        """Test avatar assignment with empty traveler dictionary."""
        traveler = {}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"  # Age defaults to 0
    
    def test_gender_case_insensitive(self, avatar_service):
        """Test that gender matching is case-insensitive."""
        traveler_upper = {"age": 25, "gender": "FEMALE"}
        avatar_upper = avatar_service.assign_avatar(traveler_upper)
        assert avatar_upper == "👩"
        
        traveler_mixed = {"age": 25, "gender": "MaLe"}
        avatar_mixed = avatar_service.assign_avatar(traveler_mixed)
        assert avatar_mixed == "👨"
    
    def test_unknown_gender_value(self, avatar_service):
        """Test avatar with unknown gender value."""
        traveler = {"age": 25, "gender": "other"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "🧑"
    
    def test_none_gender_value(self, avatar_service):
        """Test avatar with None gender value."""
        traveler = {"age": 25, "gender": None}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "🧑"
    
    def test_negative_age(self, avatar_service):
        """Test avatar with negative age (should default to infant)."""
        traveler = {"age": -1}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👶"
    
    def test_very_high_age(self, avatar_service):
        """Test avatar with very high age."""
        traveler = {"age": 100, "gender": "female"}
        avatar = avatar_service.assign_avatar(traveler)
        assert avatar == "👩"


class TestAvatarDescriptions:
    """Tests for avatar description functionality."""
    
    def test_infant_description(self, avatar_service):
        """Test description for infant avatar."""
        description = avatar_service.get_avatar_description("👶")
        assert description == "Baby"
    
    def test_child_female_description(self, avatar_service):
        """Test description for female child avatar."""
        description = avatar_service.get_avatar_description("👧")
        assert description == "Girl"
    
    def test_child_male_description(self, avatar_service):
        """Test description for male child avatar."""
        description = avatar_service.get_avatar_description("👦")
        assert description == "Boy"
    
    def test_adult_female_description(self, avatar_service):
        """Test description for female adult avatar."""
        description = avatar_service.get_avatar_description("👩")
        assert description == "Teen Girl / Woman"
    
    def test_adult_male_description(self, avatar_service):
        """Test description for male adult avatar."""
        description = avatar_service.get_avatar_description("👨")
        assert description == "Teen Boy / Man"
    
    def test_default_description(self, avatar_service):
        """Test description for default avatar."""
        description = avatar_service.get_avatar_description("🧑")
        assert description == "Person"
    
    def test_unknown_avatar_description(self, avatar_service):
        """Test description for unknown avatar."""
        description = avatar_service.get_avatar_description("🤖")
        assert description == "Person"


class TestAvatarIntegration:
    """Integration tests for avatar assignment in trip creation."""
    
    def test_family_trip_avatars(self, avatar_service):
        """Test avatar assignment for a typical family trip."""
        family = [
            {"age": 35, "gender": "male", "type": "adult"},
            {"age": 33, "gender": "female", "type": "adult"},
            {"age": 8, "gender": "female", "type": "child"},
            {"age": 5, "gender": "male", "type": "child"},
            {"age": 1, "type": "infant"}
        ]
        
        avatars = [avatar_service.assign_avatar(traveler) for traveler in family]
        
        assert avatars[0] == "👨"  # Dad
        assert avatars[1] == "👩"  # Mom
        assert avatars[2] == "👧"  # Daughter
        assert avatars[3] == "👦"  # Son
        assert avatars[4] == "👶"  # Baby
    
    def test_teen_group_avatars(self, avatar_service):
        """Test avatar assignment for a teen group trip."""
        teens = [
            {"age": 16, "gender": "male"},
            {"age": 15, "gender": "female"},
            {"age": 17, "gender": "male"},
            {"age": 14, "gender": "female"}
        ]
        
        avatars = [avatar_service.assign_avatar(traveler) for traveler in teens]
        
        assert avatars[0] == "👨"
        assert avatars[1] == "👩"
        assert avatars[2] == "👨"
        assert avatars[3] == "👩"
    
    def test_mixed_age_group_no_gender(self, avatar_service):
        """Test avatar assignment for mixed ages without gender."""
        travelers = [
            {"age": 1},
            {"age": 7},
            {"age": 15},
            {"age": 30}
        ]
        
        avatars = [avatar_service.assign_avatar(traveler) for traveler in travelers]
        
        assert avatars[0] == "👶"  # Infant
        assert avatars[1] == "🧑"  # Child (no gender)
        assert avatars[2] == "🧑"  # Teen (no gender)
        assert avatars[3] == "🧑"  # Adult (no gender)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])