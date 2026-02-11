"""LLM service for generating intelligent packing lists using OpenAI GPT-4.

RECENT UPDATES (2026-02-11):
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
        # Use gpt-4o for 40-50% speed improvement with better quality
        self.model = "gpt-4o"
    
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
        print(f"🔍 Generating list for {traveler.name} (ID: {traveler.id}, Primary: {is_primary})...")
        
        # Build focused prompt for this traveler
        prompt = self._build_single_traveler_prompt(
            traveler=traveler,
            destination=destination,
            duration=duration,
            weather_data=weather_data,
            activities=activities,
            transport=transport,
            is_primary=is_primary
        )
        
        # Call OpenAI API with streaming
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_single_traveler_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            stream=True
        )
        
        # Collect streamed response
        content = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        
        # Parse JSON from streamed content
        packing_data = self._parse_json_from_stream(content)
        
        # Extract items from response
        items = []
        categories_set = set()
        
        # Valid categories
        VALID_CATEGORIES = {
            "clothing", "toiletries", "electronics", "documents",
            "health", "comfort", "activities", "baby", "misc"
        }
        
        for item_data in packing_data.get("items", []):
            # Get and validate category
            raw_category = item_data.get("category", "misc").lower()
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
        
        This prompt implements a sophisticated family travel packing expert system that:
        - Generates personalized packing lists based on trip details
        - Calculates trip parameters (duration, season/climate, laundry access)
        - Creates comprehensive per-person lists across multiple categories
        - Adds destination & activity intelligence
        - Makes transport-specific adjustments
        
        Note: This is adapted for per-traveler parallel generation architecture.
        The original comprehensive prompt expected all travelers at once, but this
        version focuses on ONE traveler at a time for better performance.
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
**CRITICAL OUTPUT RULE: ALL items related to a specific activity MUST start with an asterisk (*) character.**
**This applies to items in ANY category (Clothing, Activities, Gear) that are activity-specific.**
**This is NON-NEGOTIABLE. Format: "*Item Name" (e.g., "*Ski/Snowboard Jacket", "*Hiking Boots", "*Wetsuit")**

**ASTERISK PREFIX REQUIREMENT - ABSOLUTELY CRITICAL:**
- ANY item that is ONLY needed for a specific activity MUST have the asterisk (*) prefix
- This includes items where the activity name is NOT in the item name itself
- Examples that MUST have asterisk: "*Helmet", "*Goggles", "*Gloves" (when for skiing/snowboarding)
- If an item like "Helmet" or "Goggles" is ONLY needed for the activity (skiing, biking, etc.), it MUST have the asterisk
- The asterisk indicates "this item is activity-specific" regardless of whether the activity name appears in the item name

**NAMING CONVENTIONS FOR ACTIVITY ITEMS:**
- **Ski/Snowboard Neutrality**: Do NOT assume "Ski" or "Snowboard". Use neutral terms:
  - "Skis" → "*Skis/Snowboard"
  - "Ski Boots" → "*Ski/Snowboard Boots"
  - "Ski Jacket" → "*Ski/Snowboard Jacket"
  - "Ski Pants" → "*Ski/Snowboard Pants"
  - "Helmet" → "*Helmet" (MUST have asterisk - it's activity-specific)
  - "Goggles" → "*Goggles" (MUST have asterisk - it's activity-specific)
  - **DO NOT include**: "Poles" or "Ski Poles" as a separate item
- **Rain Gear**: Always use "*Rain Gear" instead of "Umbrella" or "Rain Jacket" for general rain protection

For each planned activity, include necessary clothing WITH ASTERISK PREFIX:
- Skiing/Snowboarding: *Ski/Snowboard Jacket, *Ski/Snowboard Pants, *Thermal base layers (top & bottom), *Ski/Snowboard Boots, *Ski/Snowboard socks, *Gloves/mittens, *Neck warmer
- Beach/Swimming: *Swimsuit, *Swimsuit (backup), *Rash guard, *Beach cover-up, *Water shoes
- Hiking: *Hiking boots, *Moisture-wicking shirts, *Hiking pants, *Sun hat
- Water Sports: *Wetsuit, *Water shoes, *Quick-dry shorts
- Formal Events: *Dress clothes, *Dress shoes

**Age-Based Activity Clothing Rules:**
- Infants (0-2): NO activity-specific clothing (they don't participate in skiing, hiking, etc.)
- Toddlers (2-4): Very limited - assess if they can actually do the activity
- Children (5+): Include age-appropriate activity clothing WITH ASTERISK

**REMEMBER:**
1. Basic everyday clothing is ALWAYS required first
2. Activity clothing MUST have asterisk (*) prefix
3. List activity items AFTER basic items for proper grouping

## 2. TOILETRIES (category: "toiletries")
- Personal hygiene (toothbrush, toothpaste, floss, deodorant)
- Hair care (shampoo, conditioner, brush, styling products)
- Skin care (moisturizer, sunscreen, lip balm with SPF)
- Grooming (razor, shaving cream, nail clippers, tweezers)
- Feminine hygiene products (if applicable)
- Contact lens supplies (if applicable)
- Travel-sized containers and toiletry bag

**IMPORTANT: Weather-specific toiletries (sunscreen, lip balm with SPF, etc.) belong in TOILETRIES, NOT activities, even if they're important for an activity like skiing.**

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
- This app is designed for US-based travelers
- For trips WITHIN the United States, DO NOT include passport (not needed)
- For trips WITHIN the United States, travel insurance is typically optional (not essential)

**For DOMESTIC US trips, include:**
- Driver's license or state ID (mark as essential)
- Travel tickets and confirmations
- Hotel reservations
- Credit cards and cash (mark as essential)
- Emergency contact information
- Health insurance card

**For INTERNATIONAL trips (outside US), include:**
- Passport (mark as essential - check expiration date)
- Travel tickets and confirmations
- Hotel reservations
- Travel insurance documents (mark as essential for international)
- Emergency contact information
- Copies of important documents
- Credit cards and cash
- Driver's license (if driving)
- Visa (if required for destination)

**Determine if trip is domestic or international based on destination.**

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
- Comfort items specific to traveler (pacifier, lovey, etc.)

## 7. ACTIVITIES (category: "activities")
**CRITICAL: This category is for EQUIPMENT and ACCESSORIES only. Activity-specific CLOTHING goes in the CLOTHING category (marked with asterisk).**
**ALL activity-specific items (equipment, accessories, AND clothing) MUST start with asterisk (*).**

**ASTERISK PREFIX IS MANDATORY:**
- EVERY item in this category MUST have the asterisk (*) prefix
- This includes items where the activity name is NOT in the item name
- "*Helmet" - MUST have asterisk (activity-specific, even though "ski" isn't in the name)
- "*Goggles" - MUST have asterisk (activity-specific, even though "ski" isn't in the name)
- "*Gloves" - MUST have asterisk when for skiing/snowboarding (activity-specific)

**GEAR OWNERSHIP RULE (Requirement 4):**
**ASSUME THE TRAVELER OWNS ALL NECESSARY GEAR. DO NOT list "Rental voucher" or assume rentals.**
**List the ACTUAL ITEMS needed with asterisk prefix: "*Skis/Snowboard", "*Ski/Snowboard Boots", "*Helmet", etc.**

**NAMING CONVENTIONS:**
- Use "*Skis/Snowboard" not "Skis" or "Snowboard"
- Use "*Ski/Snowboard Boots" not "Ski Boots"
- Use "*Helmet" and "*Goggles" (MUST have asterisk - no "Ski" qualifier needed)
- DO NOT include "Poles" or "Ski Poles"
- Use "*Rain Gear" not "Umbrella"

**Age-Based Activity Participation Rules:**
- Infants (0-2 years): NO activity gear - they are spectators only
- Toddlers (2-4 years): Very limited activities. Assess if they can actually participate (e.g., no skiing/snowboarding for a 2yo)
- Children (5+ years): MUST include FULL SET of gear for active participation (no "rentals" assumption)
- Teens/Adults (13+): MUST include FULL SET of gear for active participation

**For EACH planned activity, include COMPREHENSIVE EQUIPMENT (assume ownership, not rentals):**

### Skiing/Snowboarding:
EQUIPMENT: *Skis/Snowboard, *Ski/Snowboard Boots, *Helmet, *Goggles, *Ski pass holder, *Hand warmers
NOTE: *Ski/Snowboard Jacket, *Ski/Snowboard Pants, *Thermal layers, *Gloves go in CLOTHING category (all marked with *)
NOTE: CRITICAL - "*Helmet" and "*Goggles" MUST have asterisk prefix even though "ski" is not in the name
NOTE: For children > 2 years old, MUST include full gear set (*Skis/Snowboard, *Ski/Snowboard Boots, *Helmet, *Goggles)
NOTE: DO NOT include "Poles" or "Ski Poles" as a separate item
NOTE: For very young children (under 2), do NOT include skiing gear - they cannot ski
NOTE: Weather-specific items like "Lip balm with SPF" and "Sunscreen" belong in TOILETRIES category, NOT activities

### Beach/Swimming:
EQUIPMENT: *Snorkel gear, *Beach toys, *Cooler, *Beach umbrella, *Beach towels
ACCESSORIES: *Waterproof phone case, *Beach bag, *Sunscreen
NOTE: *Swimsuits, *Rash guards, *Water shoes go in CLOTHING category (all marked with *)

### Hiking:
EQUIPMENT: *Hiking backpack, *Trekking poles, *Headlamp/flashlight, *First aid kit, *Map/GPS
ACCESSORIES: *Water bottles/hydration pack, *Trail snacks, *Insect repellent
NOTE: *Hiking boots, *Moisture-wicking shirts, *Hiking pants go in CLOTHING category (all marked with *)

### Water Sports (Surfing, Kayaking, etc.):
EQUIPMENT: *Sport-specific equipment (*Surfboard, *Kayak, *Life jacket, *Paddle)
ACCESSORIES: *Waterproof bag, *Towels
NOTE: *Wetsuit, *Water shoes go in CLOTHING category (all marked with *)

### Formal Events/Dining:
EQUIPMENT: *Garment bag (if needed)
NOTE: *Dress clothes and *Dress shoes go in CLOTHING category (all marked with *)

### General Outdoor Activities:
- Outdoor gear (backpack, binoculars, camera accessories)
- Games and entertainment for activities
- Guidebooks and maps
- Activity-specific safety equipment

**REMEMBER:**
1. Be COMPREHENSIVE - include ALL equipment needed for the activity
2. Check traveler AGE - don't give ski equipment to a 1-year-old
3. Activity CLOTHING goes in CLOTHING category with asterisk (*) prefix
4. Activity EQUIPMENT goes in ACTIVITIES category
5. Ensure quantities are realistic

## 8. BABY (category: "baby")
*Only for infants/toddlers - include comprehensive baby care items:*
- Diapers and wipes (sufficient quantity)
- Diaper cream and changing pad
- Baby food, formula, bottles
- Bibs and burp cloths
- Baby carrier or stroller
- Car seat (if needed)
- Baby monitor
- Pacifiers and teethers
- Baby medications (Tylenol, gas drops)
- Baby toiletries (gentle soap, lotion)

## 9. MISC (category: "misc")
- Laundry supplies (detergent pods, stain remover, clothesline)
- Plastic bags (for dirty clothes, wet items)
- Reusable shopping bags
- Rain Gear (use this instead of "Umbrella" for general rain protection)
- Sunglasses
- Travel locks and luggage tags
- Sewing kit
- Any other trip-specific items

# INTELLIGENT ADJUSTMENTS

**Weather-Based:**
- Cold weather: Add thermal layers, winter coat, gloves, warm socks
- Hot weather: Add lightweight clothing, sun protection, cooling items
- Rainy: Add Rain Gear, waterproof shoes (use "Rain Gear" not "Umbrella")
- Variable: Add versatile layers and mix of clothing

**Activity-Based (ALL activity items MUST have asterisk prefix):**
- Hiking: *Hiking boots, *Backpack, *Trekking poles, *Moisture-wicking clothing, *Water bottles, *Trail snacks, *First aid, *Sun protection
- Beach: *Swimsuits (multiple), *Beach towels, *Rash guards, *Water shoes, *Snorkel gear, *Beach toys, *Sunscreen, *Beach bag
- Skiing/Snowboarding: *Skis/Snowboard, *Ski/Snowboard Boots, *Helmet, *Goggles, *Ski/Snowboard Jacket, *Ski/Snowboard Pants, *Thermal base layers, *Ski/Snowboard socks, *Gloves, *Hand warmers, *Neck warmer (NO poles)
- Water Sports: *Wetsuit, *Water shoes, *Life jacket, *Sport-specific equipment
- Formal events: *Dress clothes, *Dress shoes, *Accessories
- Cycling: *Bike gear, *Helmet, *Cycling clothes, *Repair kit

**Age-Based Activity Exclusions:**
- Infants (0-2): No activity gear - they cannot participate in skiing, hiking, water sports, etc.
- Toddlers (2-4): Very limited - assess carefully (e.g., no skiing, limited hiking)
- Young children (5+): FULL age-appropriate gear (assume ownership, not rentals)
- Older children/teens/adults: FULL gear set (assume ownership, not rentals)

**CRITICAL RULES:**
1. Check traveler age before adding activity gear
2. For children > 2 years old doing an activity: Include FULL gear set (e.g., for skiing: *Skis/Snowboard, *Ski/Snowboard Boots, *Helmet, *Goggles - NO poles)
3. NEVER assume "rentals" - list the actual equipment items with asterisk prefix
4. Activity CLOTHING goes in CLOTHING category with asterisk (*)
5. ALL activity-specific items (in ANY category) MUST have asterisk (*) prefix
6. Use "Ski/Snowboard" neutrality - never assume one or the other
7. Use "Rain Gear" not "Umbrella"

**Transport-Based:**
- Carry-on only: Minimize quantities, travel-sized items, versatile clothing
- Checked bags: Can include bulkier items, more outfit options
- Car travel: More flexibility with quantities and bulky items
- International: Add adapters, currency, passport copies

**Age-Based:**
- Infants: Extensive baby category items, extra changes of clothes
- Toddlers: Comfort items, snacks, entertainment, potty training supplies
- Children: Age-appropriate entertainment, comfort items, kid-friendly toiletries
- Adults: Standard items plus any special needs

# OUTPUT FORMAT

Return JSON with an "items" array. Each item MUST have:
- **name**: Clear, specific item name
- **emoji**: Relevant emoji (be creative and accurate)
- **quantity**: Realistic number based on trip duration and laundry access
  - For clothing: Calculate based on duration (e.g., 7-day trip = 4-5 outfits if laundry available)
  - For consumables: Ensure sufficient quantity for entire trip
  - Use integers only (1, 2, 3, etc.)
- **category**: ONE of the 9 valid categories listed above
- **is_essential**: true for critical items that would ruin the trip if forgotten
  - Passports, medications, phone chargers, critical comfort items for young children
  - Most items should be false; reserve true for truly essential items
- **visible_to_kid**: true for most items, false only for adult-only items
  - False for: medications, adult toiletries, documents, anything inappropriate for children
- **notes**: Optional brief note with helpful context
  - Packing tips, usage suggestions, quantity rationale, alternatives

# QUALITY STANDARDS

1. **Comprehensive**: Cover ALL categories relevant to the traveler
2. **Realistic Quantities**: Base on trip duration and laundry access
3. **Age-Appropriate**: Tailor items to traveler's age and needs
4. **Activity-Specific**: Include ALL gear needed for planned activities (both equipment AND clothing)
5. **Weather-Appropriate**: Match clothing to expected conditions
6. **Practical**: Focus on items that will actually be used
7. **Organized**: Use correct categories - activity items in ACTIVITIES, basics in CLOTHING
8. **Prioritized**: Mark truly essential items correctly
9. **Age-Based Activity Logic**: Do NOT include activity gear for children too young to participate
10. **Basic Clothing Always**: ALWAYS include basic everyday clothing (underwear, socks, t-shirts, pants) even for activity-heavy trips
11. **Domestic vs International**: Check destination - no passport for US domestic trips
12. **Universal Activity Marking**: ALL activity-specific items (clothing, equipment, accessories) in ANY category MUST start with asterisk (*) - this is CRITICAL
13. **Grouping**: List basic clothing first, then activity clothing (with *) for proper visual grouping
14. **No Rentals**: Assume gear ownership - list actual items with asterisk (*Skis/Snowboard, *Ski/Snowboard Boots, *Helmet), never "rental voucher"
15. **Full Gear for Kids**: Children > 2 years old get FULL gear sets for activities they participate in
16. **Ski/Snowboard Neutrality**: Use "*Skis/Snowboard", "*Ski/Snowboard Boots", "*Ski/Snowboard Jacket", "*Ski/Snowboard Pants". Use "*Helmet" and "*Goggles" without qualifier. DO NOT include poles.
17. **Rain Gear**: Always use "Rain Gear" instead of "Umbrella" for general rain protection

# EXAMPLE OUTPUT STRUCTURE

```json
{
  "items": [
    {
      "name": "Passport",
      "emoji": "🛂",
      "quantity": 1,
      "category": "documents",
      "is_essential": true,
      "visible_to_kid": true,
      "notes": "Check expiration date before trip"
    },
    {
      "name": "T-shirts",
      "emoji": "👕",
      "quantity": 5,
      "category": "clothing",
      "is_essential": false,
      "visible_to_kid": true,
      "notes": "Mix of short and long sleeve for layering"
    }
  ]
}
```

Generate a complete, thorough packing list for this ONE traveler covering all their needs."""
    
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
        """
        Build an enhanced prompt for a single traveler that provides comprehensive context.
        
        This prompt provides all the information the LLM needs to generate a thorough,
        personalized packing list following the comprehensive system prompt guidelines.
        
        Args:
            is_primary: If True, this traveler should include shared family items
        """
        
        # Format weather with more detail
        weather_info = "Weather: Not available"
        if weather_data:
            conditions_str = ', '.join(weather_data.conditions) if weather_data.conditions else 'varied'
            weather_info = f"""Weather Forecast:
- Average Temperature: {weather_data.avg_temp}°{weather_data.temp_unit}
- Conditions: {conditions_str}"""
        
        # Determine laundry access based on duration
        laundry_note = ""
        if duration > 5:
            laundry_note = "\n- Laundry Access: Assume available every 3-4 days (plan outfit rotation accordingly)"
        elif duration > 3:
            laundry_note = "\n- Laundry Access: May be available mid-trip"
        else:
            laundry_note = "\n- Laundry Access: Not needed for short trip"
        
        # Format activities with more context
        activities_str = ', '.join(activities) if activities else 'General sightseeing and relaxation'
        
        # Format transport with more context
        transport_str = ', '.join(transport) if transport else 'Not specified (assume standard travel)'
        
        # Add age-specific guidance
        age_guidance = ""
        if traveler.age < 2:
            age_guidance = "\n\n**Special Considerations for Infant:**\n- Include comprehensive baby care items (diapers, formula, bottles, etc.)\n- Extra changes of clothes for accidents\n- Comfort items (pacifier, favorite toy, blanket)\n- Baby-safe medications and first aid"
        elif traveler.age < 5:
            age_guidance = "\n\n**Special Considerations for Toddler:**\n- Comfort items and favorite toys\n- Snacks and sippy cups\n- Potty training supplies if applicable\n- Entertainment for travel (books, small toys)\n- Extra changes of clothes"
        elif traveler.age < 13:
            age_guidance = "\n\n**Special Considerations for Child:**\n- Age-appropriate entertainment and activities\n- Comfort items from home\n- Kid-friendly toiletries\n- Appropriate clothing for activities"
        elif traveler.age < 18:
            age_guidance = "\n\n**Special Considerations for Teen:**\n- Personal electronics and chargers\n- Age-appropriate toiletries and personal care\n- Activity-specific gear\n- Some independence in packing choices"
        
        # Add primary packer guidance (Requirement 1: De-duplication)
        packer_role = ""
        if is_primary:
            packer_role = f"""
# PACKER ROLE
**PRIMARY PACKER** - You are responsible for packing SHARED FAMILY ITEMS in addition to personal items.
Include shared items such as:
- Family toiletries (toothpaste, sunscreen, shampoo - enough for the family)
- Family health items (first aid kit, family medications, hand sanitizer)
- Shared electronics (phone chargers, adapters, power banks - enough for family needs)
- Family documents (if applicable for this traveler's age/role)
- Shared miscellaneous items (laundry supplies, plastic bags, umbrella)
"""
        else:
            packer_role = f"""
# PACKER ROLE
**SECONDARY PACKER** - Focus ONLY on {traveler.name}'s PERSONAL items.
DO NOT include shared family items (family toothpaste, family first aid, shared chargers, etc.).
Only include:
- Personal toiletries (personal toothbrush, personal medications, personal care items)
- Personal electronics (if this person has their own device)
- Personal comfort items
- Personal clothing and gear
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

Planned Activities: {activities_str}
Transportation: {transport_str}

# YOUR TASK
Generate a complete, comprehensive packing list for {traveler.name} that includes:

1. **All 9 Categories** (where applicable):
   - Clothing (weather-appropriate, activity-specific, sufficient quantity)
   - Toiletries (personal hygiene, grooming, skin care)
   - Health (medications, first aid, wellness items)
   - Documents (IDs, tickets, insurance - if applicable for age)
   - Electronics (phone, chargers, entertainment devices)
   - Comfort (travel comfort, entertainment, snacks)
   - Activities (gear specific to planned activities)
   - Baby (comprehensive baby items if infant/toddler)
   - Misc (laundry supplies, bags, travel accessories)

2. **Smart Quantity Calculations**:
   - Base clothing quantities on {duration} days and laundry access
   - Ensure sufficient consumables for entire trip
   - Account for activity-specific needs

3. **Age-Appropriate Items**:
   - Tailor all items to {traveler.age}-year-old {traveler.type}
   - Include comfort items appropriate for age
   - Consider independence level and special needs

4. **Weather & Activity Adaptations**:
   - Match clothing to weather conditions
   - Include all gear needed for: {activities_str}
   - Add weather protection items as needed

5. **Essential Item Marking**:
   - Mark as essential: critical documents, medications, phone charger
   - For young children: also mark critical comfort items as essential
   - Most items should NOT be essential

Return complete JSON with "items" array following the specified format."""
        
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
    
    def _map_to_valid_category(self, raw_category: str, valid_categories: set) -> str:
        """
        Map potentially invalid category names to valid ones.
        
        Args:
            raw_category: Category name from LLM (may be invalid)
            valid_categories: Set of valid category names
        
        Returns:
            Valid category name
        """
        # If already valid, return as-is
        if raw_category in valid_categories:
            return raw_category
        
        # Map common invalid categories to valid ones
        category_mapping = {
            # Activity-related mappings
            "skiing": "activities",
            "skiing & snowboarding": "activities",
            "snowboarding": "activities",
            "hiking": "activities",
            "beach": "activities",
            "camping": "activities",
            "biking": "activities",
            "water sports": "activities",
            "sports": "activities",
            "outdoor": "activities",
            "recreation": "activities",
            "entertainment": "activities",
            
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
        
        # If contains activity-related keywords, map to activities
        activity_keywords = ["ski", "snow", "hike", "beach", "camp", "bike", "sport", "swim", "surf"]
        if any(keyword in raw_category for keyword in activity_keywords):
            print(f"⚠️  Mapped activity category '{raw_category}' → 'activities'")
            return "activities"
        # Default to misc for unknown categories
        print(f"⚠️  Unknown category '{raw_category}' → 'misc'")
        return "misc"
    
    def _parse_json_from_stream(self, content: str) -> Dict:
        """
        Parse JSON from streamed content, handling potential incomplete JSON.
        
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
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks or other wrapping
            print("🔍 DEBUG - Direct JSON parse failed, attempting to extract JSON...")
            
            # Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find raw JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, raise the original error
            print(f"❌ Failed to parse JSON from content: {content[:500]}...")
            raise Exception("Failed to parse JSON from LLM response")




# Singleton instance
llm_service = LLMService()