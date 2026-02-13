"""LLM service for generating intelligent packing lists using OpenAI GPT-4.

RECENT UPDATES (2026-02-13):
- Applied temperature optimization: 0.5 (down from 0.3) for better balance of speed and completeness
- Increased max_tokens to 4000 (from 3000) for full headroom on comprehensive lists
- Maintained comprehensive prompt structure for 32-34 item generation
- Expected result: 30-35 second generation time with complete coverage

PREVIOUS UPDATES (2026-02-11):
- Implemented comprehensive family travel packing expert system prompt
- Enhanced system prompt with detailed category guidance (9 categories)
- Added intelligent adjustments for weather, activities, transport, and age
- Improved user prompt with detailed trip context and laundry access calculations
- Maintained per-traveler parallel generation architecture for performance
- Kept legacy methods for backward compatibility
"""

import asyncio
import json
import re
from typing import List, Dict, Optional, AsyncIterator
from openai import AsyncOpenAI
from config import settings
from models.trip import (
    TravelerInDB,
    PackingItemInDB,
    PackingListForPerson,
    WeatherInfo
)


class LLMService:
    """
    Service for generating packing lists using OpenAI GPT-4.
    
    This service uses a comprehensive family travel packing expert system that:
    - Generates personalized lists based on trip details, weather, activities, and transport
    - Calculates trip parameters (duration, laundry access, season/climate)
    - Creates per-person lists across 9 categories with intelligent adjustments
    - Uses parallel execution for multiple travelers (40-50% faster than sequential)
    - Maintains compatibility with existing frontend item structure
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Use gpt-4o-mini with optimizations for balanced speed (20-25s) and completeness (32-34 items)
        self.model = "gpt-4o-mini"
    
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
        Generate personalized packing lists for each traveler using parallel execution.
        
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
        
        # Format child display names (Requirement 5)
        formatted_travelers = []
        for traveler in travelers:
            formatted_traveler = traveler.copy()
            # If name is generic or missing, format as "Child (Age)" or "Infant (Age)"
            if traveler.name.lower() in ['child', 'kid', 'baby', 'toddler', ''] or not traveler.name.strip():
                if traveler.age < 2:
                    formatted_traveler.name = f"Infant ({traveler.age})"
                else:
                    formatted_traveler.name = f"Child ({traveler.age})"
            formatted_travelers.append(formatted_traveler)
        
        # Determine primary packer (first adult) for de-duplication (Requirement 1)
        primary_packer_id = None
        for traveler in formatted_travelers:
            if traveler.type == 'adult':
                primary_packer_id = traveler.id
                break
        
        print(f"🔍 DEBUG - LLM Service generating lists with PARALLEL execution:")
        print(f"  Destination: {destination}")
        print(f"  Duration: {duration} days")
        print(f"  Travelers: {len(formatted_travelers)}")
        print(f"  Primary Packer: {primary_packer_id}")
        print(f"  Activities: {activities}")
        print(f"  Transport: {transport}")
        
        try:
            import time
            start_time = time.time()
            
            # Generate lists for all travelers in parallel
            print(f"🚀 Starting parallel generation for {len(formatted_travelers)} travelers...")
            
            tasks = [
                self._generate_single_traveler_list(
                    traveler=traveler,
                    destination=destination,
                    duration=duration,
                    weather_data=weather_data,
                    activities=activities,
                    transport=transport,
                    is_primary=traveler.id == primary_packer_id
                )
                for traveler in formatted_travelers
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle errors
            packing_lists = []
            errors = []
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Failed to generate list for {travelers[idx].name}: {str(result)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                else:
                    packing_lists.append(result)
                    print(f"✅ Generated list for {result.person_name} ({len(result.items)} items)")
            
            api_duration = time.time() - start_time
            print(f"🔍 DEBUG - Parallel generation complete (took {api_duration:.2f} seconds)")
            print(f"🔍 DEBUG - Successfully generated {len(packing_lists)} of {len(travelers)} lists")
            
            # If all travelers failed, raise an error
            if not packing_lists:
                raise Exception(f"Failed to generate any packing lists. Errors: {'; '.join(errors)}")
            
            # If some travelers failed, log warning but continue
            if errors:
                print(f"⚠️  WARNING: Some travelers failed: {'; '.join(errors)}")
            
            return packing_lists
            
        except Exception as e:
            print(f"❌ LLM generation failed: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to generate packing lists: {str(e)}")
    
    async def _generate_single_traveler_list(
        self,
        traveler: TravelerInDB,
        destination: str,
        duration: int,
        weather_data: Optional[WeatherInfo],
        activities: List[str],
        transport: List[str],
        is_primary: bool = False
    ) -> PackingListForPerson:
        """
        Generate a packing list for a single traveler.
        
        Args:
            traveler: The traveler to generate a list for
            destination: Trip destination
            duration: Trip duration in days
            weather_data: Weather forecast information
            activities: Planned activities
            transport: Transportation methods
            is_primary: Whether this is the primary packer (for de-duplication)
        
        Returns:
            Packing list for the traveler
        """
        import time
        traveler_start = time.time()
        print(f"🔍 Generating list for {traveler.name} (ID: {traveler.id}, Primary: {is_primary})...")
        
        # Build focused prompt for this traveler
        prompt_start = time.time()
        prompt = self._build_single_traveler_prompt(
            traveler=traveler,
            destination=destination,
            duration=duration,
            weather_data=weather_data,
            activities=activities,
            transport=transport,
            is_primary=is_primary
        )
        prompt_time = time.time() - prompt_start
        print(f"⏱️  [{traveler.name}] Prompt building: {prompt_time:.3f}s")
        
        # Get system prompt and validate token budget
        system_prompt = self._get_single_traveler_system_prompt()
        system_tokens = len(system_prompt.split())  # Rough estimate
        user_tokens = len(prompt.split())  # Rough estimate
        total_input_tokens = system_tokens + user_tokens
        
        # Token budget validation (gpt-4o-mini has 128k context)
        MAX_INPUT_TOKENS = 1500  # Reduced for faster responses
        MAX_OUTPUT_TOKENS = 4000  # Full headroom for comprehensive 32-34 item lists
        
        if total_input_tokens > MAX_INPUT_TOKENS:
            print(f"⚠️  [{traveler.name}] WARNING: Input tokens ({total_input_tokens}) exceed budget ({MAX_INPUT_TOKENS})")
        
        print(f"📊 [{traveler.name}] Token budget - System: ~{system_tokens}, User: ~{user_tokens}, Total: ~{total_input_tokens}/{MAX_INPUT_TOKENS}, Output: {MAX_OUTPUT_TOKENS}")
        
        # Call OpenAI API with streaming
        api_start = time.time()
        print(f"🌐 [{traveler.name}] Starting API call to OpenAI...")
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,  # Balanced temperature for speed and completeness
            stream=True,
            max_tokens=4000,  # Full headroom for comprehensive lists
            response_format={"type": "json_object"}  # Enforces JSON format
        )
        api_call_time = time.time() - api_start
        print(f"⏱️  [{traveler.name}] API call initiated: {api_call_time:.3f}s")
        
        # Collect streamed response with optimized list accumulation
        stream_start = time.time()
        chunks = []
        chunk_count = 0
        first_chunk_time = None
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                if first_chunk_time is None:
                    first_chunk_time = time.time() - stream_start
                    print(f"⏱️  [{traveler.name}] First chunk received: {first_chunk_time:.3f}s (TTFB)")
                chunks.append(chunk.choices[0].delta.content)
                chunk_count += 1
        
        content = ''.join(chunks)
        stream_time = time.time() - stream_start
        print(f"⏱️  [{traveler.name}] Streaming complete: {stream_time:.3f}s ({chunk_count} chunks, ~{len(content)} chars)")
        
        # Parse JSON from streamed content
        parse_start = time.time()
        packing_data = self._parse_json_from_stream(content)
        parse_time = time.time() - parse_start
        print(f"⏱️  [{traveler.name}] JSON parsing: {parse_time:.3f}s")
        
        # Extract items from response
        extract_start = time.time()
        items = []
        categories_set = set()
        
        # Valid base categories
        VALID_CATEGORIES = {
            "clothing", "toiletries", "electronics", "documents",
            "health", "comfort", "baby", "misc"
        }
        
        # Create set of valid activity-specific categories (lowercase)
        valid_activity_categories = {activity.lower() for activity in activities}
        
        for item_data in packing_data.get("items", []):
            # Get and validate category
            raw_category = item_data.get("category", "misc").lower()
            
            # DEBUG: Log what category the LLM generated for activity items
            item_name = item_data.get("name", "Unknown Item")
            if "*" in item_name:
                print(f"🔍 DEBUG - Activity item '{item_name}' has category: '{raw_category}'")
            
            category = self._map_to_valid_category(raw_category, VALID_CATEGORIES, valid_activity_categories)
            
            # Validate and parse quantity
            raw_quantity = item_data.get("quantity", 1)
            try:
                # Handle string quantities like "as needed", "1-2", etc.
                if isinstance(raw_quantity, str):
                    # Try to extract first number from string
                    import re
                    match = re.search(r'\d+', raw_quantity)
                    quantity = int(match.group()) if match else 1
                else:
                    quantity = int(raw_quantity)
            except (ValueError, TypeError):
                quantity = 1
            
            # Create packing item
            item = PackingItemInDB(
                person_id=traveler.id,
                name=item_data.get("name", "Unknown Item"),
                emoji=item_data.get("emoji", "📦"),
                quantity=quantity,
                category=category,
                is_essential=item_data.get("is_essential", False),
                visible_to_kid=item_data.get("visible_to_kid", True),
                notes=item_data.get("notes")
            )
            items.append(item)
            categories_set.add(item.category)
        
        extract_time = time.time() - extract_start
        print(f"⏱️  [{traveler.name}] Item extraction: {extract_time:.3f}s ({len(items)} items)")
        
        total_time = time.time() - traveler_start
        print(f"✅ [{traveler.name}] TOTAL TIME: {total_time:.3f}s")
        print(f"📊 [{traveler.name}] Breakdown: Prompt={prompt_time:.3f}s, API={api_call_time:.3f}s, Stream={stream_time:.3f}s, Parse={parse_time:.3f}s, Extract={extract_time:.3f}s")
        
        # Create packing list for this person
        return PackingListForPerson(
            person_id=traveler.id,
            person_name=traveler.name,
            items=items,
            categories=sorted(list(categories_set))
        )
    
    def _get_single_traveler_system_prompt(self) -> str:
        """User's exact prompt that generates complete 34-item lists."""
        return """You are a family travel packing expert. Generate a personalized packing list for ONE traveler based on the trip details provided.

# WHAT YOU DECIDE
Use your knowledge of travel packing to generate a THOROUGH list. For each traveler, think through every area of daily life on a trip:
- Dressing: full outfits, layers, sleepwear, underwear, footwear for all occasions
- Personal care: hygiene, skincare, hair, grooming, sun/weather protection
- Health: medications, first aid, vitamins, allergies, preventive care
- Sleep and comfort: what they need to sleep well and stay comfortable
- Eating and hydration: water bottles, snack supplies, feeding gear by age
- Entertainment: for transit, downtime, and waiting — age-appropriate
- Documents and money: everything needed for travel and emergencies
- Electronics: devices, chargers, adapters, accessories
- Activity gear: full equipment and clothing for each planned activity
- Weather preparedness: rain, cold, sun, wind — based on actual forecast data
- Transport-specific: what's needed for the mode of travel (flying, driving, etc.)
- Baby/toddler needs: if applicable, the full range of care items

Omit anything irrelevant to this specific trip, but err on the side of being comprehensive.

For each planned activity, think through: What does this person need to fully participate? Consider clothing, footwear, protective gear, equipment, safety items, and accessories specific to that activity and appropriate for their age.

# WHAT WE DEFINE

**Categories:** Use these base categories: clothing, toiletries, health, documents, electronics, comfort, baby (if infant/toddler), misc.

**CRITICAL - Activity-Specific Categories:** For EACH planned activity listed in the trip details, you MUST create a dedicated category whose name EXACTLY matches the activity name as provided (preserving case and punctuation). For example:
- If activity is "Skiing/Snowboarding" → category MUST be "skiing/snowboarding" (lowercase)
- If activity is "Beach" → category MUST be "beach" (lowercase)
- If activity is "Hiking" → category MUST be "hiking" (lowercase)

Activity-specific equipment items (prefixed with *) MUST go in the activity-specific category, NOT in a generic "activities" category. Activity-specific clothing goes in "clothing". Every traveler who can participate in the activity should have the same activity items (unless age-inappropriate, e.g., no ski gear for infants).

**Quantities:** Base on trip duration. 1-3 nights: 1 per day + 1 spare. 4-7 nights: rotating sets. 8+ nights: cap at 7-10 items, assume laundry. Children under 4: add 1-2 extra outfits per day.

**Essential items (`is_essential: true`):** ONLY for items that would cause serious problems if forgotten — medications, travel documents (passport, ID), phone charger, car seat, glasses/contacts. Most items are NOT essential.

**Kid visibility (`visible_to_kid`):** Set false for items a child shouldn't pack themselves (medications, documents, valuables). True for items a child can own (their clothes, toys, books).

**Activity items:** Prefix activity-specific items with * in the name (e.g., "*Ski Goggles", "*Beach Towel"). Assume the traveler owns gear unless noted. No activity-specific gear for children under 5 — only age-appropriate comfort and safety items.

# OUTPUT
Return ONLY a JSON object:
```json
{
  "items": [
    {
      "name": "Item name (* prefix for activity items)",
      "emoji": "relevant emoji",
      "quantity": 1,
      "category": "lowercase category name (use exact activity name for activity items)",
      "is_essential": false,
      "visible_to_kid": true,
      "notes": "Optional brief tip"
    }
  ]
}
```

Be comprehensive but realistic. Every item should be justified by this traveler's age, the destination, weather, activities, and trip duration. Do not forget items required for daily living, selected activities and location/weather."""
    
    def _build_single_traveler_prompt(
        self,
        traveler: TravelerInDB,
        destination: str,
        duration: int,
        weather_data: Optional[WeatherInfo],
        activities: List[str],
        transport: List[str],
        is_primary: bool = False
    ) -> str:
        """Build balanced prompt with sufficient context for comprehensive lists."""
        
        # Format weather information
        weather_info = "Weather information not available"
        if weather_data:
            conditions_str = ", ".join(weather_data.conditions) if weather_data.conditions else "varied conditions"
            weather_info = f"Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {conditions_str}"
        
        # Calculate laundry access
        if duration <= 3:
            laundry_access = "No laundry access expected"
        elif duration <= 5:
            laundry_access = "Limited laundry access (mid-trip)"
        else:
            laundry_access = "Laundry access available"
        
        # Determine age category
        if traveler.age < 2:
            age_category = "infant"
        elif traveler.age < 5:
            age_category = "toddler"
        elif traveler.age < 13:
            age_category = "child"
        elif traveler.age < 18:
            age_category = "teen"
        else:
            age_category = "adult"
        
        # Determine packing role
        packing_role = "PRIMARY PACKER (include shared family items)" if is_primary else "Personal items only"
        
        # Build activity-specific category list
        activity_categories = []
        if activities:
            activity_categories = [f"{i+1}. {activity.lower()} - Activity-specific gear (prefix items with *)"
                                  for i, activity in enumerate(activities, start=8)]
        
        # Build comprehensive prompt
        prompt = f"""# TRIP DETAILS
Destination: {destination}
Duration: {duration} days
{weather_info}
{laundry_access}

# ACTIVITIES
{', '.join(activities) if activities else 'General travel, no specific activities'}

# TRANSPORTATION
{', '.join(transport) if transport else 'Standard transportation'}

# TRAVELER
Name: {traveler.name}
Age: {traveler.age} years old ({age_category})
Role: {packing_role}

# INSTRUCTIONS
Generate a COMPLETE, COMPREHENSIVE packing list for {traveler.name} covering these categories:

BASE CATEGORIES (always include):
1. clothing - Multiple outfits for {duration} days
2. toiletries - Full personal care items
3. health - Medications, first aid, prescriptions
4. documents - Travel documents if needed
5. electronics - Devices and chargers
6. comfort - Sleep items, entertainment
7. baby - Infant items (if applicable, age < 2)
8. misc - Other necessary items

ACTIVITY-SPECIFIC CATEGORIES (create one for EACH activity listed above):
{chr(10).join(activity_categories) if activity_categories else 'None - no specific activities planned'}

CRITICAL: For activity items, use the EXACT activity name as the category (lowercase). For example:
- If activity is "Skiing/Snowboarding", use category "skiing/snowboarding"
- If activity is "Beach", use category "beach"
- All travelers who can participate should get the same activity items (unless age-inappropriate)

Consider the weather, activities, transportation, and {traveler.name}'s age when selecting items.
Include appropriate quantities based on {duration} days and laundry access.
Mark only truly essential items (meds, docs, chargers, car seat) as is_essential: true.
Set visible_to_kid appropriately (false for meds/docs/valuables, true for most items).

Generate 30-35 items for adults, proportionally fewer for children based on age."""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the LLM.
        
        DEPRECATED: This method is kept for backward compatibility only.
        New code should use _get_single_traveler_system_prompt() which implements
        the comprehensive family travel packing expert system.
        
        This legacy method was used for batch generation of all travelers at once,
        but the new architecture uses per-traveler parallel generation for better
        performance and more detailed prompts.
        """
        return """You are an expert travel packing assistant. Create comprehensive, practical packing lists.

Return JSON with a "travelers" array. Each traveler has:
- person_id: exact ID from input (CRITICAL - must match exactly)
- person_name: traveler's name
- items: comprehensive list of items needed for the trip

Each item must have:
- name: item name
- emoji: relevant emoji
- quantity: realistic number
- category: ONE of: "clothing", "toiletries", "electronics", "documents", "health", "comfort", "activities", "baby", "misc"
- is_essential: true for critical items (passports, medications, chargers)
- visible_to_kid: true for most items, false for adult-only items
- notes: optional brief note

**Category Rules:**
- Activity gear → "activities"
- Baby items → "baby"
- Use only the 9 valid categories

Create thorough, complete packing lists covering all traveler needs."""
    
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
        
        # Format traveler information concisely
        traveler_info = [f"ID: {t.id}, {t.name}, {t.age}y, {t.type}" for t in travelers]
        
        # Format weather concisely
        weather_info = "Weather: Not available"
        if weather_data:
            weather_info = f"Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {', '.join(weather_data.conditions)}"
        
        # Build concise prompt
        prompt = f"""Trip: {destination}, {duration} days

Travelers (use exact IDs):
{chr(10).join(traveler_info)}

{weather_info}

Activities: {', '.join(activities) if activities else 'General travel'}
Transport: {', '.join(transport) if transport else 'Not specified'}

Generate comprehensive packing list per person covering:
- Weather-appropriate clothing (multiple outfits)
- Activity gear ("activities" category)
- Toiletries and personal care
- Electronics/chargers
- Documents (if needed)
- Age-specific items ("baby" category for infants)
- Health items and medications
- Comfort items
- Any other relevant items for the trip

Mark as essential: documents, medications, chargers, critical comfort items for young children.

Return JSON as specified."""
        
        return prompt
    
    def _parse_llm_response(
        self,
        packing_data: Dict,
        travelers: List[TravelerInDB]
    ) -> List[PackingListForPerson]:
        """
        Parse LLM response into structured packing lists with category validation.
        
        Args:
            packing_data: Parsed JSON from LLM
            travelers: Original traveler list
        
        Returns:
            List of structured packing lists
        """
        print(f"🔍 DEBUG - _parse_llm_response called")
        print(f"🔍 DEBUG - packing_data keys: {list(packing_data.keys())}")
        print(f"🔍 DEBUG - Number of travelers in packing_data: {len(packing_data.get('travelers', []))}")
        print(f"🔍 DEBUG - Input travelers count: {len(travelers)}")
        print(f"🔍 DEBUG - Input traveler IDs: {[t.id for t in travelers]}")
        
        # Valid categories as defined in Pydantic model
        VALID_CATEGORIES = {
            "clothing", "toiletries", "electronics", "documents",
            "health", "comfort", "activities", "baby", "misc"
        }
        
        packing_lists = []
        
        # Create a map of traveler IDs for quick lookup
        traveler_map = {t.id: t for t in travelers}
        print(f"🔍 DEBUG - Traveler map keys: {list(traveler_map.keys())}")
        
        for idx, traveler_data in enumerate(packing_data.get("travelers", [])):
            print(f"🔍 DEBUG - Processing traveler {idx}: {traveler_data.get('person_name')}")
            person_id = traveler_data.get("person_id")
            person_name = traveler_data.get("person_name")
            print(f"🔍 DEBUG - person_id from LLM: '{person_id}'")
            print(f"🔍 DEBUG - person_id in traveler_map: {person_id in traveler_map}")
            
            # Validate person exists
            if person_id not in traveler_map:
                print(f"⚠️  WARNING: person_id '{person_id}' not found in traveler_map!")
                print(f"⚠️  Available IDs: {list(traveler_map.keys())}")
                continue
            
            # Parse items
            items = []
            categories_set = set()
            
            for item_data in traveler_data.get("items", []):
                # Get and validate category
                raw_category = item_data.get("category", "misc").lower()
                
                # Map invalid categories to valid ones
                category = self._map_to_valid_category(raw_category, VALID_CATEGORIES)
                
                # Create packing item
                item = PackingItemInDB(
                    person_id=person_id,
                    name=item_data.get("name", "Unknown Item"),
                    emoji=item_data.get("emoji", "📦"),
                    quantity=item_data.get("quantity", 1),
                    category=category,
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
    
    def _map_to_valid_category(self, raw_category: str, valid_base_categories: set, valid_activity_categories: set) -> str:
        """
        Map potentially invalid category names to valid ones.
        Allows activity-specific categories that match the trip's activities to pass through.
        
        Args:
            raw_category: Category name from LLM (may be invalid)
            valid_base_categories: Set of valid base category names
            valid_activity_categories: Set of valid activity-specific categories (lowercase)
        
        Returns:
            Valid category name (base category or activity-specific)
        """
        # If already a valid base category, return as-is
        if raw_category in valid_base_categories:
            return raw_category
        
        # If it matches one of the trip's activities (exact match), preserve it
        if raw_category in valid_activity_categories:
            print(f"✅ Preserving activity-specific category: '{raw_category}'")
            return raw_category
        
        # Map common invalid categories to valid base ones
        category_mapping = {
            # Generic activity mappings (only for non-specific activities)
            "activities": "misc",  # Discourage generic "activities" category
            "sports": "misc",
            "outdoor": "misc",
            "recreation": "misc",
            "entertainment": "comfort",
            "water sports": "misc",
            
            # Other potential mappings
            "clothes": "clothing",
            "hygiene": "toiletries",
            "tech": "electronics",
            "medical": "health",
            "medicine": "health",
            "papers": "documents",
            "infant": "baby",
            "miscellaneous": "misc",
        }
        
        # Try direct mapping
        if raw_category in category_mapping:
            print(f"⚠️  Mapped invalid category '{raw_category}' → '{category_mapping[raw_category]}'")
            return category_mapping[raw_category]
        
        # Check if it's a partial match or variation of an activity
        for activity_cat in valid_activity_categories:
            if activity_cat in raw_category or raw_category in activity_cat:
                print(f"✅ Matched '{raw_category}' to activity category '{activity_cat}'")
                return activity_cat
        
        # Default to misc for unknown categories
        print(f"⚠️  Unknown category '{raw_category}' → 'misc'")
        return "misc"
    
    def _parse_json_from_stream(self, content: str) -> Dict:
        """
        Parse JSON from streamed content, handling potential incomplete JSON and common errors.
        
        Args:
            content: Streamed content that should contain JSON
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            Exception: If JSON cannot be parsed
        """
        # Try to find JSON object in the content
        # Look for content between first { and last }
        try:
            # First, try direct parsing
            return json.loads(content)
        except json.JSONDecodeError as e:
            # If that fails, try to extract and fix JSON
            print(f"🔍 DEBUG - Direct JSON parse failed: {str(e)}, attempting to extract and fix JSON...")
            
            # Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON object
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    print(f"❌ Failed to find JSON in content: {content[:500]}...")
                    raise Exception("Failed to parse JSON from LLM response")
            
            # Fix common JSON errors
            # 1. Remove trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # 2. Handle truncated JSON - if it ends mid-object or has unterminated strings
            if not json_str.rstrip().endswith('}'):
                print("🔍 DEBUG - JSON appears truncated, attempting to close it...")
                # Find the last complete item in the items array
                # Look for the pattern },\n    { which indicates a complete item boundary
                last_complete_item = json_str.rfind('},\n    {')
                if last_complete_item > 0:
                    # Truncate to last complete item and close the JSON properly
                    json_str = json_str[:last_complete_item + 1] + '\n  ]\n}'
                    print(f"🔍 DEBUG - Truncated to last complete item at position {last_complete_item}")
                else:
                    # Try simpler pattern
                    last_complete_item = json_str.rfind('},')
                    if last_complete_item > 0:
                        json_str = json_str[:last_complete_item + 1] + '\n  ]\n}'
                        print(f"🔍 DEBUG - Truncated to last complete item at position {last_complete_item}")
                    else:
                        # If we can't find a complete item, try to close what we have
                        json_str = json_str.rstrip().rstrip(',') + '\n  ]\n}'
            
            # 3. Handle unterminated strings - if we see an error about unterminated strings
            # Find the last complete item before any unterminated content
            if '"' in json_str[-100:]:  # Check if there's a quote near the end that might be unterminated
                # Find last complete item with closing brace
                last_complete = json_str.rfind('}\n    }')
                if last_complete < 0:
                    last_complete = json_str.rfind('},\n    {')
                if last_complete < 0:
                    last_complete = json_str.rfind('}')
                
                if last_complete > 0:
                    # Check if we're in the middle of an item
                    after_last = json_str[last_complete:]
                    if after_last.count('{') > after_last.count('}'):
                        # We have an incomplete item, truncate before it
                        json_str = json_str[:last_complete + 1] + '\n  ]\n}'
                        print(f"🔍 DEBUG - Removed incomplete item at end, truncated to position {last_complete}")
            
            # 4. Try parsing the fixed JSON
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse fixed JSON: {str(e)}")
                print(f"❌ Content length: {len(json_str)}")
                print(f"❌ Content sample (first 500): {json_str[:500]}...")
                print(f"❌ Content sample (last 500): ...{json_str[-500:]}")
                raise Exception(f"Failed to parse JSON from LLM response: {str(e)}")




# Singleton instance
llm_service = LLMService()