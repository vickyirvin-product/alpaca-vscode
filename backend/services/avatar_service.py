"""Avatar service for smart avatar assignment based on traveler attributes."""
from typing import Optional


class AvatarService:
    """Service for assigning appropriate avatars to travelers."""
    
    # Avatar mappings by age group and gender
    INFANT_AVATAR = "👶"  # 0-2 years
    CHILD_FEMALE_AVATAR = "👧"  # 3-12 years, female
    CHILD_MALE_AVATAR = "👦"  # 3-12 years, male
    TEEN_FEMALE_AVATAR = "👩"  # 13-17 years, female
    TEEN_MALE_AVATAR = "👨"  # 13-17 years, male
    ADULT_FEMALE_AVATAR = "👩"  # 18+ years, female
    ADULT_MALE_AVATAR = "👨"  # 18+ years, male
    DEFAULT_AVATAR = "🧑"  # Unknown gender or unspecified
    
    def assign_avatar(self, traveler: dict) -> str:
        """
        Assign an appropriate emoji avatar based on traveler attributes.
        
        Args:
            traveler: Dictionary containing traveler information with keys:
                - age: int (required)
                - gender: str (optional, values: "male", "female", or None)
                - type: str (optional, values: "adult", "child", "infant")
        
        Returns:
            str: Emoji avatar character
            
        Logic:
            - Infants (0-2): 👶
            - Children (3-12): 👧 (female) or 👦 (male)
            - Teens (13-17): 👩 (female) or 👨 (male)
            - Adults (18+): 👩 (female) or 👨 (male)
            - Default: 🧑 (if gender unknown)
        """
        age = traveler.get("age", 0)
        gender = traveler.get("gender", "").lower() if traveler.get("gender") else None
        traveler_type = traveler.get("type", "").lower() if traveler.get("type") else None
        
        # Infants (0-2 years) - gender-neutral baby
        if age <= 2 or traveler_type == "infant":
            return self.INFANT_AVATAR
        
        # Children (3-12 years)
        elif 3 <= age <= 12 or traveler_type == "child":
            if gender == "female":
                return self.CHILD_FEMALE_AVATAR
            elif gender == "male":
                return self.CHILD_MALE_AVATAR
            else:
                return self.DEFAULT_AVATAR
        
        # Teens (13-17 years)
        elif 13 <= age <= 17:
            if gender == "female":
                return self.TEEN_FEMALE_AVATAR
            elif gender == "male":
                return self.TEEN_MALE_AVATAR
            else:
                return self.DEFAULT_AVATAR
        
        # Adults (18+ years)
        elif age >= 18 or traveler_type == "adult":
            if gender == "female":
                return self.ADULT_FEMALE_AVATAR
            elif gender == "male":
                return self.ADULT_MALE_AVATAR
            else:
                return self.DEFAULT_AVATAR
        
        # Default fallback
        return self.DEFAULT_AVATAR
    
    def get_avatar_description(self, avatar: str) -> str:
        """
        Get a human-readable description of an avatar.
        
        Args:
            avatar: Emoji avatar character
            
        Returns:
            str: Description of the avatar
        """
        descriptions = {
            self.INFANT_AVATAR: "Baby",
            self.CHILD_FEMALE_AVATAR: "Girl",
            self.CHILD_MALE_AVATAR: "Boy",
            self.TEEN_FEMALE_AVATAR: "Teen Girl / Woman",
            self.TEEN_MALE_AVATAR: "Teen Boy / Man",
            self.ADULT_FEMALE_AVATAR: "Woman",
            self.ADULT_MALE_AVATAR: "Man",
            self.DEFAULT_AVATAR: "Person"
        }
        return descriptions.get(avatar, "Person")


# Singleton instance
avatar_service = AvatarService()