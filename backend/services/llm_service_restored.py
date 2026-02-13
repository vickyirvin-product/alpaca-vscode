"""LLM service for generating intelligent packing lists using OpenAI GPT-4.

RESTORATION (2026-02-13):
- Restored original comprehensive prompt that generated 34 items
- Applied ONLY temperature optimization: 0.5 (down from 0.7)
- Kept max_tokens at 4000 for full headroom
- Maintained all comprehensive instructions for completeness
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
        # Use gpt-4o-mini with temperature optimization for speed while maintaining completeness
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
        MAX_INPUT_TOKENS = 2000  # Allow more tokens for comprehensive prompt
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
            temperature=0.5,  # Balanced temperature for speed and completeness (down from 0.7)
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
        
        # Valid base categories - activity-specific categories are also allowed
        VALID_CATEGORIES = {
            "clothing", "toiletries", "electronics", "documents",
            "health", "comfort", "activities", "baby", "misc"
        }
        
        for item_data in packing_data.get("items", []):
            # Get and validate category
            raw_category = item_data.get("category", "misc").lower()
            
            # DEBUG: Log what category the LLM generated for activity items
            item_name = item_data.get("name", "Unknown Item")
            if "*" in item_name or any(keyword in item_name.lower() for keyword in ["ski", "snowboard", "helmet", "goggles"]):
                print(f"🔍 DEBUG - Activity item '{item_name}' has category: '{raw_category}'")
            
            category = self._map_to_valid_category(raw_category, VALID_CATEGORIES)
            
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
        """
        Get the comprehensive system prompt for single traveler list generation.
        
        This is the ORIGINAL comprehensive prompt that generated 34 items in 47 seconds.
        We're keeping it exactly as-is for completeness, only optimizing the API parameters.
        """
        return """You are a comprehensive family travel packing expert. Generate a detailed, personalized packing list for ONE traveler based on their specific needs, trip details, weather, activities, and transportation.

# YOUR ROLE
You are an expert at creating practical, comprehensive packing lists that account for:
- Trip duration and climate/season
- Traveler age, type (adult/child/infant), and specific needs
- Weather conditions and temperature ranges
- Planned activities and required gear
- Transportation methods and luggage constraints
- Laundry access and outfit rotation strategies
- Essential vs. optional items prioritization

# TRIP ANALYSIS
Before generating items, analyze:
1. **Duration**: Calculate days and determine outfit rotation (laundry every 3-4 days if >5 days)
2. **Season/Climate**: Determine appropriate clothing layers and weather gear
3. **Activities**: Identify specialized gear needed (hiking boots, swimwear, ski gear, etc.)
4. **Transport**: Adjust for luggage constraints (carry-on only, checked bags, car travel)
5. **Traveler Profile**: Age-appropriate items, special needs, comfort items

# CATEGORIES & ITEMS TO INCLUDE

Generate items across these categories (use ONLY these 9 valid categories):

## 1. CLOTHING (category: "clothing")
**CRITICAL: ALWAYS include comprehensive basic everyday clothing, then add activity-specific clothing items.**

**STRUCTURE YOUR CLOTHING LIST IN THIS ORDER:**

### PART 1: BASIC EVERYDAY CLOTHING (list these FIRST)
**Core basics - ALWAYS include for EVERY traveler (even for activity-heavy trips):**

**Undergarments (adjust quantity for trip duration and laundry access):**
- Underwear (sufficient for trip duration)
- Bras (for women/girls) - at least 2-3, including sports bra if active
- Regular socks (sufficient for trip duration)
- Undershirts/camisoles (if applicable)

**Tops - Weather-Driven Selection:**
- **Hot weather (>75°F):** Short-sleeve t-shirts, tank tops, lightweight blouses, breathable fabrics
- **Moderate weather (60-75°F):** Mix of short and long-sleeve shirts, light sweaters
- **Cold weather (<60°F):** Long-sleeve shirts, sweaters, thermal tops for layering
- **All weather:** At least one nice casual top for dining out

**Bottoms - Weather-Driven Selection:**
- **Hot weather (>75°F):** Shorts, skirts, lightweight pants, capris
- **Moderate weather (60-75°F):** Mix of pants and shorts, jeans
- **Cold weather (<60°F):** Long pants, jeans, warm leggings/tights
- **All weather:** At least one nice pair for dining out

**Sleepwear:**
- Pajamas or sleepwear appropriate for climate
- **Hot weather:** Lightweight, breathable sleepwear
- **Cold weather:** Warm pajamas or thermal sleepwear

**Footwear - Context-Driven:**
- Everyday walking shoes or sneakers (comfortable for sightseeing)
- **Beach/warm destinations:** Sandals or flip-flops
- **Cold/wet destinations:** Waterproof or warm boots for general use
- **Formal activities:** Dress shoes if needed
- Slippers or indoor shoes (if staying in rental/hotel)

**Outerwear - Weather-Driven:**
- **Hot weather (>75°F):** Light cardigan or sun protection layer
- **Moderate weather (60-75°F):** Light jacket or sweater
- **Cold weather (<60°F):** Warm jacket or coat for general use
- **Rainy destinations:** Rain jacket or waterproof layer

**Accessories - Weather & Activity-Driven:**
- **Hot/sunny:** Sun hat, sunglasses (mark sunglasses as essential)
- **Cold weather:** Warm hat, scarf, gloves for general use
- **All weather:** Belt (if needed), everyday jewelry
- **Beach:** Beach hat, cover-up

**Smart Quantity Calculations:**
- Short trips (1-3 days): 1 outfit per day + 1 spare
- Medium trips (4-7 days): Outfit rotation with laundry consideration
- Long trips (8+ days): Cap at 7-10 outfits, assume laundry access
- Undergarments: Always sufficient for trip duration (or laundry cycle)

### PART 2: ACTIVITY-SPECIFIC CLOTHING (list these AFTER basics)
**CRITICAL: Activity items MUST start with asterisk (*) for proper frontend display.**

For each planned activity, include necessary clothing WITH ASTERISK PREFIX:
- Skiing/Snowboarding: *Ski/Snowboard Jacket, *Ski/Snowboard Pants, *Thermal base layers, *Ski/Snowboard Boots, *Ski/Snowboard socks, *Gloves, *Neck warmer
- Beach/Swimming: *Swimsuit, *Swimsuit (backup), *Rash guard, *Beach cover-up, *Water shoes
- Hiking: *Hiking boots, *Moisture-wicking shirts, *Hiking pants, *Sun hat
- Water Sports: *Wetsuit, *Water shoes, *Quick-dry shorts
- Formal Events: *Dress clothes, *Dress shoes

**Age-Based Activity Clothing Rules:**
- Infants (0-2): NO activity-specific clothing (they don't participate)
- Toddlers (2-4): Very limited - assess if they can actually do the activity
- Children (5+): Include age-appropriate activity clothing WITH ASTERISK

## 2. TOILETRIES (category: "toiletries")
- Personal hygiene (toothbrush, toothpaste, floss, deodorant)
- Hair care (shampoo, conditioner, brush, styling products)
- Skin care (moisturizer, sunscreen, lip balm with SPF)
- Grooming (razor, shaving cream, nail clippers, tweezers)
- Feminine hygiene products (if applicable)
- Contact lens supplies (if applicable)
- Travel-sized containers and toiletry bag

## 3. HEALTH (category: "health")
- Prescription medications (with extras)
- First aid supplies (bandages, antiseptic, pain relievers)
- Vitamins and supplements
- Motion sickness remedies
- Allergy medications
- Insect repellent
- Hand sanitizer and wipes
- Face masks (if needed)
- Medical documents and insurance cards

## 4. DOCUMENTS (category: "documents")
**US DOMESTIC TRAVEL RULES:**
- For trips WITHIN the United States, DO NOT include passport
- For trips WITHIN the United States, travel insurance is optional

**For DOMESTIC US trips, include:**
- Driver's license or state ID (mark as essential)
- Travel tickets and confirmations
- Hotel reservations
- Credit cards and cash (mark as essential)
- Emergency contact information
- Health insurance card

**For INTERNATIONAL trips, include:**
- Passport (mark as essential)
- Travel tickets and confirmations
- Hotel reservations
- Travel insurance documents (mark as essential)
- Emergency contact information
- Copies of important documents
- Credit cards and cash
- Driver's license (if driving)
- Visa (if required)

## 5. ELECTRONICS (category: "electronics")
- Phone and charger (mark as essential)
- Tablet/laptop and chargers
- Camera and accessories
- Headphones/earbuds
- Power bank/portable charger
- Universal adapter (for international travel)
- E-reader
- Charging cables and organizer

## 6. COMFORT (category: "comfort")
- Travel pillow and blanket
- Eye mask and earplugs
- Favorite stuffed animal/toy (for children)
- Books, magazines, or entertainment
- Snacks for travel
- Reusable water bottle
- Comfort items specific to traveler

## 7. ACTIVITIES (category: "activities")
**CRITICAL: Equipment items MUST start with asterisk (*). Assume travelers own gear.**

For EACH planned activity, include COMPREHENSIVE EQUIPMENT:

### Skiing/Snowboarding:
*Skis/Snowboard, *Ski/Snowboard Boots, *Helmet, *Goggles, *Ski pass holder, *Hand warmers
NOTE: Children > 2 years old get FULL gear set. DO NOT include poles.

### Beach/Swimming:
*Snorkel gear, *Beach toys, *Cooler, *Beach umbrella, *Beach towels, *Waterproof phone case

### Hiking:
*Hiking backpack, *Trekking poles, *Headlamp, *First aid kit, *Map/GPS, *Water bottles, *Trail snacks

### Water Sports:
*Sport-specific equipment, *Life jacket, *Waterproof bag

**Age-Based Activity Rules:**
- Infants (0-2): NO activity gear
- Toddlers (2-4): Very limited
- Children (5+): FULL age-appropriate gear set

## 8. BABY (category: "baby")
*Only for infants/toddlers:*
- Diapers and wipes (sufficient quantity)
- Diaper cream and changing pad
- Baby food, formula, bottles
- Bibs and burp cloths
- Baby carrier or stroller
- Car seat (if needed)
- Baby monitor
- Pacifiers and teethers
- Baby medications
- Baby toiletries

## 9. MISC (category: "misc")
- Laundry supplies
- Plastic bags
- Reusable shopping bags
- Rain Gear
- Sunglasses
- Travel locks and luggage tags
- Sewing kit
- Any other trip-specific items

# INTELLIGENT ADJUSTMENTS

**Weather-Based:**
- Cold: thermal layers, winter coat, gloves, warm socks
- Hot: lightweight clothing, sun protection
- Rainy: Rain Gear, waterproof shoes
- Variable: versatile layers

**Activity-Based (ALL with asterisk):**
- Include ALL necessary equipment and clothing
- Check traveler age before adding gear
- Assume gear ownership, not rentals

**Transport-Based:**
- Carry-on only: minimize quantities
- Checked bags: more flexibility
- Car travel: bulkier items OK

**Age-Based:**
- Infants: extensive baby items, extra clothes
- Toddlers: comfort items, snacks, entertainment
- Children: age-appropriate items
- Adults: standard items plus special needs

# OUTPUT FORMAT

Return JSON with "items" array. Each item MUST have:
- **name**: Clear, specific item name (with * for activity items)
- **emoji**: Relevant emoji
- **quantity**: Realistic integer based on trip duration
- **category**: ONE of the 9 valid categories
- **is_essential**: true only for critical items (meds, docs, chargers, car seat)
- **visible_to_kid**: false for meds/docs/valuables, true for most items
- **notes**: Optional helpful tip

# QUALITY STANDARDS

1. **Comprehensive**: Cover ALL categories relevant to traveler
2. **Realistic Quantities**: Base on trip duration and laundry access
3. **Age-Appropriate**: Tailor to traveler's age and needs
4. **Activity-Specific**: Include ALL gear for planned activities
5. **Weather-Appropriate**: Match clothing to conditions
6. **Practical**: Focus on items that will be used
7. **Organized**: Use correct categories
8. **Prioritized**: Mark truly essential items correctly
9. **Basic Clothing Always**: ALWAYS include everyday basics
10. **Domestic vs International**: Check destination for passport
11. **Activity Marking**: ALL activity items start with asterisk (*)
12. **No Rentals**: List actual gear items
13. **Full Gear for Kids**: Children > 2 get full gear sets

Generate 30-35 items for adults, proportionally fewer for children based on age."""
    
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
        """Build comprehensive prompt with full context for thorough lists."""
        
        # Format weather with detail
        weather_info = "Weather: Not available"
        if weather_data:
            conditions_str = ', '.join(weather_data.conditions) if weather_data.conditions else 'varied'
            weather_info = f"""Weather Forecast:
- Average Temperature: {weather_data.avg_temp}°{weather_data.temp_unit}
- Conditions: {conditions_str}"""
        
        # Determine laundry access
        laundry_note = ""
        if duration > 5:
            laundry_note = "\n- Laundry Access: Assume available every 3-4 days"
        elif duration > 3:
            laundry_note = "\n- Laundry Access: May be available mid-trip"
        else:
            laundry_note = "\n- Laundry Access: Not needed for short trip"
        
        # Format activities
        activities_str = ', '.join(activities) if activities else 'General sightseeing and relaxation'
        
        # Format transport
        transport_str = ', '.join(transport) if transport else 'Not specified'
        
        # Add age-specific guidance
        age_guidance = ""
        if traveler.age < 2:
            age_guidance = "\n\n**Special Considerations for Infant:**\n- Include comprehensive baby care items\n- Extra changes of clothes\n- Comfort items\n- Baby-safe medications"
        elif traveler.age < 5:
            age_guidance = "\n\n**Special Considerations for Toddler:**\n- Comfort items and toys\n- Snacks and sippy cups\n- Potty training supplies if applicable\n- Entertainment for travel\n- Extra changes of clothes"
        elif traveler.age < 13:
            age_guidance = "\n\n**Special Considerations for Child:**\n- Age-appropriate entertainment\n- Comfort items from home\n- Kid-friendly toiletries\n- Appropriate clothing for activities"
        elif traveler.age < 18:
            age_guidance = "\n\n**Special Considerations for Teen:**\n- Personal electronics and chargers\n- Age-appropriate toiletries\n- Activity-specific gear\n- Some independence in choices"
        
        # Add primary packer guidance
        packer_role = ""
        if is_primary:
            packer_role = f"""
# PACKER ROLE
**PRIMARY PACKER** - Include SHARED FAMILY ITEMS:
- Family toiletries (toothpaste, sunscreen, shampoo)
- Family health items (first aid kit, medications, hand sanitizer)
- Shared electronics (chargers, adapters, power banks)
- Family documents (if applicable)
- Shared miscellaneous items (laundry supplies, plastic bags)
"""
        else:
            packer_role = f"""
# PACKER ROLE
**SECONDARY PACKER** - Focus ONLY on {traveler.name}'s PERSONAL items.
DO NOT include shared family items.
"""
        
        # Build comprehensive prompt
        prompt = f"""# TRIP DETAILS
Destination: {destination}
Duration: {duration} days{laundry_note}

# TRAVELER PROFILE
Name: {traveler.name}
Age: {traveler.age} years old
Type: {traveler.type}
{age_guidance}
{packer_role}

# TRIP CONDITIONS
{weather_info}

# PLANNED ACTIVITIES
{activities_str}

# TRANSPORTATION
{transport_str}

# INSTRUCTIONS
Generate a COMPLETE, COMPREHENSIVE packing list for {traveler.name} covering ALL 9 categories:
1. clothing - Multiple outfits for {duration} days (basics FIRST, then activity items with *)
2. toiletries - Full personal care items
3. health - Medications, first aid, prescriptions
4. documents - Travel documents if needed
5. electronics - Devices and chargers
6. comfort - Sleep items, entertainment
7. baby - Infant items (if applicable)
8. activities - Activity-specific gear (prefix items with *)
9. misc - Other necessary items

Consider the weather, activities, transportation, and {traveler.name}'s age when selecting items.
Include appropriate quantities based on {duration} days and laundry access.
Mark only truly essential items (meds, docs, chargers, car seat) as is_essential: true.
Set visible_to_kid appropriately (false for meds/docs/valuables, true for most items).

Generate 30-35 items for adults, proportionally fewer for children based on age."""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """DEPRECATED: Legacy method kept for backward compatibility."""
        return """You are an expert travel packing assistant. Create comprehensive, practical packing lists.

Return JSON with a "travelers" array. Each traveler has:
- person_id: exact ID from input
- person_name: traveler's name
- items: comprehensive list of items

Each item must have:
- name: item name
- emoji: relevant emoji
- quantity: realistic number
- category: ONE of: "clothing", "toiletries", "electronics", "documents", "health", "comfort", "activities", "baby", "misc"
- is_essential: true for critical items
- visible_to_kid: true for most items, false for adult-only items
- notes: optional brief note

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
        """DEPRECATED: Legacy method kept for backward compatibility."""
        traveler_info = [f"ID: {t.id}, {t.name}, {t.age}y, {t.type}" for t in travelers]
        weather_info = "Weather: Not available"
        if weather_data:
            weather_info = f"Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {', '.join(weather_data.conditions)}"
        
                prompt = f"""Trip: {destination}, {duration} days
                
        Travelers: {', '.join(traveler_info)}
        {weather_info}
        Activities: {', '.join(activities)}
        Transport: {', '.join(transport)}
        
        Create comprehensive packing lists for all travelers, covering all categories and considering weather, activities, and duration."""
                
                return prompt
            
            def _parse_json_from_stream(self, content: str) -> Dict:
                """Extract JSON from streamed content, handling partial responses."""
                try:
                    # Try to parse the entire content as JSON
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON object from content
                    # Look for the first { and last }
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        try:
                            json_str = content[start_idx:end_idx+1]
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            pass
                    
                    # If we still can't parse, return a default structure
                    print(f"❌ Failed to parse JSON from stream. Content preview: {content[:200]}")
                    return {"items": []}
            
            def _map_to_valid_category(self, category: str, valid_categories: set) -> str:
                """Map any category string to one of the valid categories."""
                category_lower = category.lower().strip()
                
                # Direct match
                if category_lower in valid_categories:
                    return category_lower
                
                # Fuzzy matching
                category_mappings = {
                    "clothes": "clothing",
                    "apparel": "clothing",
                    "fashion": "clothing",
                    "wear": "clothing",
                    "gear": "activities",
                    "equipment": "activities",
                    "tools": "activities",
                    "hygiene": "toiletries",
                    "personal care": "toiletries",
                    "grooming": "toiletries",
                    "medical": "health",
                    "medicine": "health",
                    "medications": "health",
                    "wellness": "health",
                    "papers": "documents",
                    "id": "documents",
                    "passport": "documents",
                    "tech": "electronics",
                    "gadgets": "electronics",
                    "devices": "electronics",
                    "relax": "comfort",
                    "rest": "comfort",
                    "entertainment": "comfort",
                    "leisure": "comfort",
                    "infant": "baby",
                    "toddler": "baby",
                    "child care": "baby",
                    "other": "misc",
                    "miscellaneous": "misc"
                }
                
                for key, mapped_category in category_mappings.items():
                    if key in category_lower:
                        return mapped_category
                
                # Default to misc if no match
                return "misc"

