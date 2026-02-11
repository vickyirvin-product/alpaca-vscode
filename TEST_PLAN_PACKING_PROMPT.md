# Test Plan: Comprehensive Packing List System Prompt

## 1. Overview
This test plan validates the new 212-line family travel packing expert system prompt. The system is designed to generate intelligent, personalized packing lists based on trip details, weather, activities, transport, and traveler profiles.

**System Capabilities:**
- **9 Detailed Categories:** Clothing, Toiletries, Health, Documents, Electronics, Comfort, Activities, Baby, Misc.
- **Intelligent Adjustments:** Adapts to weather forecasts, planned activities, and transportation modes.
- **Smart Quantities:** Calculates clothing needs based on trip duration and laundry access.
- **Age-Appropriate Logic:** Customizes items for infants, toddlers, children, teens, and adults.
- **Parallel Generation:** Uses per-traveler parallel execution for performance.

## 2. Test Scenarios

We will test the system across a matrix of variables to ensure robustness and accuracy.

### Scenario A: The "Standard" Family Vacation
*   **Trip:** 7 days, Beach Resort (Hot/Sunny), Plane travel.
*   **Travelers:** Family of 4 (Dad, Mom, Child 8yo, Toddler 3yo).
*   **Activities:** Swimming, Dining Out.
*   **Goal:** Verify baseline functionality, age differentiation, and hot weather logic.

### Scenario B: The "Adventure" Trip
*   **Trip:** 4 days, Mountains (Cold/Snowy), Car travel.
*   **Travelers:** Couple (Adult 1, Adult 2).
*   **Activities:** Hiking, Skiing.
*   **Goal:** Verify cold weather logic, activity-specific gear (skiing/hiking), and car travel flexibility.

### Scenario C: The "Long Haul" International
*   **Trip:** 14 days, European City Tour (Variable/Rainy), Plane + Train.
*   **Travelers:** Solo Adult or Parent + Teen.
*   **Activities:** Walking tours, Museums.
*   **Goal:** Verify duration-based quantity limits (laundry logic), rain gear, international travel items (adapters, passports), and train travel constraints.

### Scenario D: The "Quick" Business/Solo Trip
*   **Trip:** 1 night, City (Temperate), Plane (Carry-on only implied).
*   **Travelers:** Single Adult.
*   **Activities:** Business meeting (implied by context or explicit).
*   **Goal:** Verify minimal quantity calculations and "carry-on" optimization.

### Scenario E: The "Infant" Edge Case
*   **Trip:** 5 days, Visit Grandparents (Indoor/Temperate), Car.
*   **Travelers:** Mom + Infant (<1 year).
*   **Activities:** None specific.
*   **Goal:** Verify comprehensive "Baby" category generation (diapers, formula, etc.) and safety/medical items.

## 3. Validation Criteria

For each generated list, we will verify:

### 3.1 Content Accuracy
- **Category Coverage:** All 9 categories must be present (where applicable). "Baby" category should only appear for infants/toddlers.
- **Age Appropriateness:**
    - *Infants:* Diapers, wipes, formula, carrier.
    - *Kids:* Toys, books, kid-friendly toiletries.
    - *Adults:* IDs, credit cards, electronics.
- **Weather Adaptation:**
    - *Hot:* Sunscreen, swimsuits, shorts, sandals.
    - *Cold:* Thermal layers, coats, gloves, boots.
    - *Rain:* Umbrella, rain jacket, waterproof shoes.
- **Activity Specifics:**
    - *Beach:* Towels, sand toys, goggles.
    - *Skiing:* Skis/rental info, helmet, goggles, hand warmers.
    - *Hiking:* Boots, backpack, water bottle.

### 3.2 Quantity Logic
- **Clothing:**
    - Short trips (<4 days): 1 outfit per day + 1 spare.
    - Medium trips (5-7 days): Full coverage or outfit rotation.
    - Long trips (7+ days): Capped quantities assuming laundry (e.g., 5-7 outfits max).
- **Consumables:** Diapers/wipes quantity should scale with days (approx 6-8 diapers/day).

### 3.3 Critical Marking (`is_essential`)
- **Must be True:** Passports, Tickets, Prescription Meds, Phone/Charger.
- **Must be True (Kids):** Critical comfort object (pacifier, lovey).
- **Must be False:** T-shirts, socks (unless specialized), generic toiletries.

### 3.4 Data Integrity
- **JSON Structure:** Valid JSON object with an `items` array.
- **Fields:** `name`, `emoji`, `quantity` (int), `category` (valid enum), `is_essential` (bool), `visible_to_kid` (bool), `notes` (string/null).
- **Emoji:** Every item must have a relevant emoji.

## 4. Test Data

### Input for Scenario A (Beach Family)
```json
{
  "destination": "Maui, Hawaii",
  "start_date": "2026-06-01",
  "end_date": "2026-06-08",
  "weather_data": {
    "avg_temp": 85,
    "temp_unit": "F",
    "conditions": ["sunny", "clear"]
  },
  "activities": ["Beach", "Pool", "Snorkeling", "Casual Dining"],
  "transport": ["Plane", "Rental Car"],
  "travelers": [
    {"id": "t1", "name": "Dad", "age": 40, "type": "adult"},
    {"id": "t2", "name": "Mom", "age": 38, "type": "adult"},
    {"id": "t3", "name": "Leo", "age": 8, "type": "child"},
    {"id": "t4", "name": "Mia", "age": 3, "type": "child"}
  ]
}
```

### Input for Scenario B (Ski Trip)
```json
{
  "destination": "Aspen, Colorado",
  "start_date": "2026-12-10",
  "end_date": "2026-12-14",
  "weather_data": {
    "avg_temp": 25,
    "temp_unit": "F",
    "conditions": ["snowy", "cloudy"]
  },
  "activities": ["Skiing", "Après-ski", "Hot Tub"],
  "transport": ["Car"],
  "travelers": [
    {"id": "t1", "name": "Alex", "age": 30, "type": "adult"},
    {"id": "t2", "name": "Sam", "age": 30, "type": "adult"}
  ]
### Input for Scenario C (Long Haul Euro Trip)
```json
{
  "destination": "London & Paris",
  "start_date": "2026-09-01",
  "end_date": "2026-09-15",
  "weather_data": {
    "avg_temp": 65,
    "temp_unit": "F",
    "conditions": ["rainy", "cloudy", "mild"]
  },
  "activities": ["Museums", "Walking Tours", "Fine Dining", "Train Travel"],
  "transport": ["Plane", "Train", "Public Transit"],
  "travelers": [
    {"id": "t1", "name": "Sarah", "age": 45, "type": "adult"},
    {"id": "t2", "name": "Jake", "age": 16, "type": "adult"} 
  ]
}
```
*Note: Teen is modeled as "adult" type but age 16 triggers teen-specific prompt logic.*

### Input for Scenario D (Quick Business Trip)
```json
{
  "destination": "New York City, NY",
  "start_date": "2026-03-10",
  "end_date": "2026-03-11",
  "weather_data": {
    "avg_temp": 50,
    "temp_unit": "F",
    "conditions": ["cloudy"]
  },
  "activities": ["Business Meetings", "Dinner"],
  "transport": ["Plane", "Taxi"],
  "travelers": [
    {"id": "t1", "name": "Michael", "age": 35, "type": "adult"}
  ]
}
```

### Input for Scenario E (Infant Visit)
```json
{
  "destination": "Chicago, IL",
  "start_date": "2026-05-20",
  "end_date": "2026-05-25",
  "weather_data": {
    "avg_temp": 70,
    "temp_unit": "F",
    "conditions": ["sunny", "windy"]
  },
  "activities": ["Family Visit", "Park Stroll"],
  "transport": ["Car"],
  "travelers": [
    {"id": "t1", "name": "Mom", "age": 32, "type": "adult"},
    {"id": "t2", "name": "Baby Sam", "age": 0, "type": "infant"}
  ]
}
```
}
```

## 5. Expected Outcomes & Benchmarks

| Metric | Target | Acceptable Range |
| :--- | :--- | :--- |
| **Generation Speed** | ~3-5s per person (Parallel) | < 25s Total for 4 people |
| **Item Count** | 25-40 items per person | 20-50 items |
| **Category Accuracy** | 100% Valid Categories | 0 Invalid Categories |
| **Essential Accuracy** | Key Docs/Meds Marked | No false positives on generic items |

## 6. Edge Cases to Verify

1.  **Missing Weather Data:** System should default to "variable" packing (layers) rather than failing or assuming sunny.
2.  **No Activities Listed:** System should provide a solid "General Travel" baseline.
3.  **Cross-Gender/Age Norms:** Ensure "Feminine Hygiene" isn't assigned to male profiles (if gender is inferable/provided, otherwise generic "Toiletries" should suffice). *Note: Current model has limited gender context, reliance is on generic coverage.*
4.  **Extreme Durations:**
    - 1 Day: Should not suggest "Laundry Detergent".
    - 30 Days: Should not suggest 30 pairs of underwear (Max out at ~7-10).
5.  **Large Families:** Performance test with 6-8 travelers to ensure parallel execution doesn't timeout.

## 7. Execution Strategy

Since the system uses OpenAI GPT-4o, tests are non-deterministic but should be directionally consistent.

1.  **Manual Spot Check:** Run Scenario A and B once manually via the UI/API to verify general quality.
2.  **Automated Validation:** (Future Phase) Implement a test script that runs these payloads against the `_generate_single_traveler_list` function and asserts the JSON structure and category presence.