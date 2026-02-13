import {
  Snowflake,
  Sun,
  Mountain,
  Waves,
  Bike,
  Tent,
  Dumbbell,
  Utensils,
  Camera,
  Sparkles,
  LucideIcon
} from 'lucide-react';

/**
 * Maps activity keywords to lucide-react icons.
 * Used to display activity-specific icons for packing items.
 */
export const activityIconMap: Record<string, LucideIcon> = {
  // Winter Sports - expanded to include gear items
  ski: Snowflake,
  snow: Snowflake,
  snowboard: Snowflake,
  winter: Snowflake,
  helmet: Snowflake,  // Ski/snowboard helmet
  goggle: Snowflake,  // Ski/snowboard goggles
  glove: Snowflake,   // Ski/snowboard gloves
  mitt: Snowflake,    // Ski/snowboard mittens
  warmer: Snowflake,  // Hand/toe warmers for skiing
  boot: Snowflake,    // Ski/snowboard boots (when in context)
  
  // Beach & Water
  beach: Sun,
  swim: Waves,
  surf: Waves,
  snorkel: Waves,
  dive: Waves,
  kayak: Waves,
  water: Waves,
  wetsuit: Waves,
  
  // Hiking & Outdoor
  hike: Mountain,
  hiking: Mountain,
  climb: Mountain,
  trek: Mountain,
  mountain: Mountain,
  trail: Mountain,
  
  // Cycling
  bike: Bike,
  cycling: Bike,
  
  // Camping
  camp: Tent,
  camping: Tent,
  
  // Fitness
  gym: Dumbbell,
  workout: Dumbbell,
  fitness: Dumbbell,
  yoga: Dumbbell,
  
  // Dining
  dining: Utensils,
  restaurant: Utensils,
  formal: Utensils,
  
  // Photography
  photo: Camera,
  photography: Camera,
};

/**
 * Detects if an item name starts with an asterisk (activity-specific marker)
 * and returns the cleaned name and associated activity icon.
 */
export function parseActivityItem(itemName: string): {
  isActivityItem: boolean;
  cleanName: string;
  ActivityIcon: LucideIcon | null;
} {
  // Check if item starts with asterisk
  if (!itemName.startsWith('*')) {
    return {
      isActivityItem: false,
      cleanName: itemName,
      ActivityIcon: null,
    };
  }
  
  // Remove asterisk
  const cleanName = itemName.substring(1).trim();
  
  // Find matching activity icon based on keywords
  const lowerName = cleanName.toLowerCase();
  let ActivityIcon: LucideIcon | null = null;
  
  for (const [keyword, icon] of Object.entries(activityIconMap)) {
    if (lowerName.includes(keyword)) {
      ActivityIcon = icon;
      break;
    }
  }
  
  return {
    isActivityItem: true,
    cleanName,
    ActivityIcon,
  };
}

/**
 * Gets an appropriate icon for a category name.
 * Used for dynamic activity-specific categories that aren't in the hardcoded categoryLabels.
 */
export const getCategoryIcon = (category: string): string => {
  const categoryLower = category.toLowerCase();
  
  // Map common activity categories to icons
  if (categoryLower.includes('ski')) return '⛷️';
  if (categoryLower.includes('snowboard')) return '🏂';
  if (categoryLower.includes('beach')) return '🏖️';
  if (categoryLower.includes('swim')) return '🏊';
  if (categoryLower.includes('hik')) return '🥾';
  if (categoryLower.includes('camp')) return '⛺';
  if (categoryLower.includes('bike') || categoryLower.includes('cycl')) return '🚴';
  if (categoryLower.includes('climb')) return '🧗';
  if (categoryLower.includes('fish')) return '🎣';
  if (categoryLower.includes('golf')) return '⛳';
  if (categoryLower.includes('tennis')) return '🎾';
  if (categoryLower.includes('run')) return '🏃';
  
  // Default activity icon
  return '🎯';
};