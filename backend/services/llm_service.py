"""LLM service for generating intelligent packing lists using OpenAI GPT-4."""

import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from config import settings
from models.trip import (
    TravelerInDB,
    PackingItemInDB,
    PackingListForPerson,
    WeatherInfo
)


class LLMService:
    """Service for generating packing lists using OpenAI GPT-4."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"
    
    async def generate_packing_lists(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        travelers: List[TravelerInDB],
        weather_data: Optional[WeatherInfo],
        activities: List[str],
        transport: List[str]
    ) -> List[PackingListForPerson]:
        """
        Generate personalized packing lists for each traveler.
        
        Args:
            destination: Trip destination
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            travelers: List of travelers
            weather_data: Weather forecast information
            activities: Planned activities
            transport: Transportation methods
        
        Returns:
            List of packing lists, one per traveler
        """
        # Calculate trip duration
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        duration = (end - start).days + 1
        
        # Build comprehensive prompt
        prompt = self._build_prompt(
            destination=destination,
            duration=duration,
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            packing_data = json.loads(content)
            
            # Convert to structured format
            packing_lists = self._parse_llm_response(packing_data, travelers)
            
            return packing_lists
            
        except Exception as e:
            # Fallback to basic packing list if LLM fails
            print(f"LLM generation failed: {str(e)}")
            return self._generate_fallback_lists(travelers, duration)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an expert travel packing assistant. Your job is to create comprehensive, 
personalized packing lists for families going on trips. Consider:

1. Each person's age and needs (adults, children, infants have different requirements)
2. Weather conditions and temperature
3. Trip duration and activities
4. Transportation method
5. Destination-specific requirements

Generate practical, organized packing lists with:
- Appropriate quantities based on trip length
- Age-appropriate items for each traveler
- Essential items clearly marked
- Items organized by category
- Helpful emojis for visual appeal
- Special considerations (medications, comfort items for kids, etc.)

Return your response as a JSON object with a "travelers" array, where each traveler has:
- person_id: matching the input traveler ID
- person_name: traveler's name
- items: array of packing items

Each item should have:
- name: item name
- emoji: relevant emoji
- quantity: number needed
- category: one of [clothing, toiletries, electronics, documents, health, comfort, activities, baby, misc]
- is_essential: boolean (true for critical items like passports, medications)
- visible_to_kid: boolean (true for most items, false for adult-only items)
- notes: optional helpful note

Be thorough but practical. Consider the specific needs of each family member."""
    
    def _build_prompt(
        self,
        destination: str,
        duration: int,
        travelers: List[TravelerInDB],
        weather_data: Optional[WeatherInfo],
        activities: List[str],
        transport: List[str]
    ) -> str:
        """Build the user prompt with all context."""
        
        # Format traveler information
        traveler_info = []
        for t in travelers:
            traveler_info.append(
                f"- {t.name}: {t.age} years old ({t.type})"
            )
        
        # Format weather information
        weather_info = "Weather information not available"
        if weather_data:
            conditions_str = ", ".join(weather_data.conditions)
            weather_info = f"""Weather Forecast:
- Average Temperature: {weather_data.avg_temp}°{weather_data.temp_unit}
- Conditions: {conditions_str}
- Recommendation: {weather_data.recommendation}"""
        
        # Build the prompt
        prompt = f"""Create personalized packing lists for a family trip with the following details:

DESTINATION: {destination}
DURATION: {duration} days ({duration} nights)

TRAVELERS:
{chr(10).join(traveler_info)}

{weather_info}

PLANNED ACTIVITIES:
{chr(10).join(f"- {activity}" for activity in activities) if activities else "- General sightseeing and relaxation"}

TRANSPORTATION:
{chr(10).join(f"- {method}" for method in transport) if transport else "- Not specified"}

Please generate a comprehensive packing list for each traveler. Consider:
1. The weather conditions and pack appropriate clothing
2. Each person's age and specific needs
3. The trip duration (pack enough but consider laundry options for longer trips)
4. Activities planned (hiking gear, beach items, etc.)
5. Essential documents and medications
6. Comfort items for children
7. Electronics and chargers
8. Toiletries and personal care items

For children, include:
- Comfort items (stuffed animals, blankets)
- Age-appropriate entertainment
- Extra clothing (kids get messy!)
- Snacks for travel

For infants, include:
- Diapers and wipes
- Formula/baby food
- Bottles and sippy cups
- Baby carrier
- Changing pad

Mark items as essential if they are:
- Travel documents (passports, tickets)
- Medications
- Critical comfort items for young children
- Important electronics (phone chargers)

Return the packing lists in JSON format as specified in the system prompt."""
        
        return prompt
    
    def _parse_llm_response(
        self,
        packing_data: Dict,
        travelers: List[TravelerInDB]
    ) -> List[PackingListForPerson]:
        """
        Parse LLM response into structured packing lists.
        
        Args:
            packing_data: Parsed JSON from LLM
            travelers: Original traveler list
        
        Returns:
            List of structured packing lists
        """
        packing_lists = []
        
        # Create a map of traveler IDs for quick lookup
        traveler_map = {t.id: t for t in travelers}
        
        for traveler_data in packing_data.get("travelers", []):
            person_id = traveler_data.get("person_id")
            person_name = traveler_data.get("person_name")
            
            # Validate person exists
            if person_id not in traveler_map:
                continue
            
            # Parse items
            items = []
            categories_set = set()
            
            for item_data in traveler_data.get("items", []):
                # Create packing item
                item = PackingItemInDB(
                    person_id=person_id,
                    name=item_data.get("name", "Unknown Item"),
                    emoji=item_data.get("emoji", "📦"),
                    quantity=item_data.get("quantity", 1),
                    category=item_data.get("category", "misc"),
                    is_essential=item_data.get("is_essential", False),
                    visible_to_kid=item_data.get("visible_to_kid", True),
                    notes=item_data.get("notes")
                )
                items.append(item)
                categories_set.add(item.category)
            
            # Create packing list for this person
            packing_list = PackingListForPerson(
                person_id=person_id,
                person_name=person_name,
                items=items,
                categories=sorted(list(categories_set))
            )
            packing_lists.append(packing_list)
        
        return packing_lists
    
    def _generate_fallback_lists(
        self,
        travelers: List[TravelerInDB],
        duration: int
    ) -> List[PackingListForPerson]:
        """
        Generate basic fallback packing lists if LLM fails.
        
        Args:
            travelers: List of travelers
            duration: Trip duration in days
        
        Returns:
            Basic packing lists
        """
        packing_lists = []
        
        for traveler in travelers:
            items = []
            categories = set()
            
            # Basic items for everyone
            basic_items = [
                ("Underwear", "🩲", min(duration + 2, 10), "clothing"),
                ("Socks", "🧦", min(duration + 2, 10), "clothing"),
                ("T-Shirts", "👕", min(duration, 7), "clothing"),
                ("Pants/Shorts", "👖", max(3, duration // 3), "clothing"),
                ("Pajamas", "🩱", max(2, duration // 4), "clothing"),
                ("Shoes", "👟", 2, "clothing"),
                ("Jacket", "🧥", 1, "clothing"),
                ("Toiletry Bag", "🧴", 1, "toiletries"),
                ("Toothbrush", "🪥", 1, "toiletries"),
                ("Phone Charger", "🔌", 1, "electronics"),
            ]
            
            # Add age-specific items
            if traveler.type == "infant":
                basic_items.extend([
                    ("Diapers", "🍼", duration * 8, "baby"),
                    ("Baby Wipes", "🧻", 5, "baby"),
                    ("Baby Food", "🍎", duration * 3, "baby"),
                    ("Bottles", "🍼", 3, "baby"),
                ])
            elif traveler.type == "child":
                basic_items.extend([
                    ("Favorite Toy", "🧸", 1, "comfort"),
                    ("Activity Book", "📚", 2, "activities"),
                ])
            
            # Create items
            for name, emoji, quantity, category in basic_items:
                item = PackingItemInDB(
                    person_id=traveler.id,
                    name=name,
                    emoji=emoji,
                    quantity=quantity,
                    category=category,
                    is_essential=category in ["documents", "health"]
                )
                items.append(item)
                categories.add(category)
            
            packing_list = PackingListForPerson(
                person_id=traveler.id,
                person_name=traveler.name,
                items=items,
                categories=sorted(list(categories))
            )
            packing_lists.append(packing_list)
        
        return packing_lists


# Singleton instance
llm_service = LLMService()