/**
 * Utility functions for trip-related operations
 */

/**
 * Determines the season based on a date
 */
function getSeason(date: Date): 'Winter' | 'Spring' | 'Summer' | 'Fall' {
  const month = date.getMonth(); // 0-11
  
  // December (11), January (0), February (1)
  if (month === 11 || month === 0 || month === 1) {
    return 'Winter';
  }
  // March (2), April (3), May (4)
  if (month >= 2 && month <= 4) {
    return 'Spring';
  }
  // June (5), July (6), August (7)
  if (month >= 5 && month <= 7) {
    return 'Summer';
  }
  // September (8), October (9), November (10)
  return 'Fall';
}

/**
 * Extracts city name from destination string
 * Handles formats like "Tokyo, Japan" or "Paris, France" or just "London"
 */
function extractCityName(destination: string): string {
  // Split by comma and take the first part (city name)
  const parts = destination.split(',');
  return parts[0].trim();
}

/**
 * Generates a formatted trip title based on season and destination
 * Format: "<Season> Trip to <City Name>"
 * 
 * @param destination - The trip destination (e.g., "Tokyo, Japan")
 * @param startDate - The trip start date (ISO string)
 * @returns Formatted trip title (e.g., "Spring Trip to Tokyo")
 */
export function generateTripTitle(destination: string, startDate: string): string {
  const date = new Date(startDate);
  const season = getSeason(date);
  const cityName = extractCityName(destination);
  
  return `${season} Trip to ${cityName}`;
}

/**
 * Generates a short trip title for cases with multiple cities
 * If the title is too long, it truncates with "..."
 * 
 * @param destination - The trip destination
 * @param startDate - The trip start date (ISO string)
 * @param maxLength - Maximum length before truncation (default: 30)
 * @returns Formatted trip title, possibly truncated
 */
export function generateShortTripTitle(
  destination: string,
  startDate: string,
  maxLength: number = 30
): string {
  const fullTitle = generateTripTitle(destination, startDate);
  
  if (fullTitle.length <= maxLength) {
    return fullTitle;
  }
  
  // Truncate and add ellipsis
  return fullTitle.substring(0, maxLength - 3) + '...';
}