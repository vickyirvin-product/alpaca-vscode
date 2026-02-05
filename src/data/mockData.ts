import { TripInfo, PackingItem, PackingList, Traveler, ItemCategory } from '@/types/packing';

// Import avatar images
import momAvatar from '@/assets/avatars/mom.jpeg';
import dadAvatar from '@/assets/avatars/dad.jpeg';
import emmaAvatar from '@/assets/avatars/emma.jpeg';
import lucasAvatar from '@/assets/avatars/lucas.jpg';

export const mockTravelers: Traveler[] = [
  { id: 'mom', name: 'Mom (Sarah)', age: 38, type: 'adult', avatar: momAvatar },
  { id: 'dad', name: 'Dad (Mike)', age: 40, type: 'adult', avatar: dadAvatar },
  { id: 'emma', name: 'Emi', age: 10, type: 'child', avatar: emmaAvatar },
  { id: 'lucas', name: 'Cam', age: 12, type: 'child', avatar: lucasAvatar },
];

export const mockTrip: TripInfo = {
  id: 'trip-001',
  destination: 'Tokyo, Japan',
  startDate: '2026-03-28',
  endDate: '2026-04-18',
  duration: 21,
  weather: {
    avgTemp: 15,
    tempUnit: 'C',
    conditions: ['sunny', 'rainy', 'cloudy'],
    recommendation: 'Pack layers! Cherry blossom season means mild days but cool evenings. Rain is common.',
  },
  travelers: mockTravelers,
  createdAt: new Date().toISOString(),
};

// Extended trip data for the dashboard
export const extendedTripData = {
  title: 'Spring Trip to Japan',
  locations: ['Tokyo', 'Kyoto', 'Koyasan'],
  activities: ['Hiking', 'Sightseeing'],
  weather: {
    lowRange: { min: 30, max: 33 },
    highRange: { min: 59, max: 62 },
    unit: 'F' as const,
  },
  travelers: {
    adults: 2,
    kids: [
      { name: 'Emi', age: 10 },
      { name: 'Cam', age: 12 },
    ],
  },
};

const createItem = (
  id: string,
  personId: string,
  name: string,
  emoji: string,
  quantity: number,
  category: ItemCategory,
  isEssential = false,
  isPacked = false,
  visibleToKid = true
): PackingItem => ({
  id,
  personId,
  name,
  emoji,
  quantity,
  category,
  isEssential,
  isPacked,
  visibleToKid,
});

export const mockPackingItems: PackingItem[] = [
  // Mom's items
  createItem('m1', 'mom', 'Passports (Family)', '🛂', 4, 'documents', true),
  createItem('m2', 'mom', 'Travel Insurance Docs', '📄', 1, 'documents', true),
  createItem('m3', 'mom', "Cam's Allergy Meds", '💊', 1, 'health', true),
  createItem('m4', 'mom', 'First Aid Kit', '🩹', 1, 'health', true),
  createItem('m5', 'mom', 'T-Shirts', '👕', 7, 'clothing'),
  createItem('m6', 'mom', 'Light Jacket', '🧥', 1, 'clothing'),
  createItem('m7', 'mom', 'Raincoat', '🌧️', 1, 'clothing'),
  createItem('m8', 'mom', 'Comfortable Walking Shoes', '👟', 2, 'clothing'),
  createItem('m9', 'mom', 'Toiletry Bag', '🧴', 1, 'toiletries'),
  createItem('m10', 'mom', 'Phone Charger', '🔌', 1, 'electronics'),
  createItem('m11', 'mom', 'Universal Power Adapter', '🔋', 2, 'electronics', true),
  createItem('m12', 'mom', 'Camera', '📷', 1, 'electronics'),
  createItem('m13', 'mom', 'Laundry Bag', '👜', 1, 'misc'),
  createItem('m14', 'mom', 'Detergent Sheets', '🧼', 10, 'misc'),

  // Dad's items
  createItem('d1', 'dad', 'T-Shirts', '👕', 7, 'clothing'),
  createItem('d2', 'dad', 'Jeans', '👖', 3, 'clothing'),
  createItem('d3', 'dad', 'Light Jacket', '🧥', 1, 'clothing'),
  createItem('d4', 'dad', 'Sneakers', '👟', 1, 'clothing'),
  createItem('d5', 'dad', 'Sandals', '🩴', 1, 'clothing'),
  createItem('d6', 'dad', 'Toiletry Kit', '🧴', 1, 'toiletries'),
  createItem('d7', 'dad', 'Sunglasses', '🕶️', 1, 'clothing'),
  createItem('d8', 'dad', 'Day Backpack', '🎒', 1, 'misc'),
  createItem('d9', 'dad', 'Portable Battery Pack', '🔋', 2, 'electronics'),
  createItem('d10', 'dad', 'Headphones', '🎧', 1, 'electronics'),

  // Emi's items (10 years old)
  createItem('e1', 'emma', 'Bunny (Lovey)', '🐰', 1, 'comfort', true),
  createItem('e2', 'emma', 'T-Shirts', '👕', 7, 'clothing'),
  createItem('e3', 'emma', 'Shorts/Skirts', '👗', 5, 'clothing'),
  createItem('e4', 'emma', 'Light Jacket', '🧥', 1, 'clothing'),
  createItem('e5', 'emma', 'Raincoat', '🌧️', 1, 'clothing'),
  createItem('e6', 'emma', 'Pajamas', '🩱', 3, 'clothing'),
  createItem('e7', 'emma', 'Underwear', '🩲', 8, 'clothing'),
  createItem('e8', 'emma', 'Sneakers', '👟', 1, 'clothing'),
  createItem('e9', 'emma', 'Activity Books', '📚', 3, 'activities'),
  createItem('e10', 'emma', 'Tablet + Charger', '📱', 1, 'electronics'),
  createItem('e11', 'emma', 'Kids Headphones', '🎧', 1, 'electronics'),
  createItem('e12', 'emma', 'Sunscreen (Kids)', '☀️', 1, 'toiletries'),

  // Cam's items (12 years old)
  createItem('l1', 'lucas', 'Gaming Console', '🎮', 1, 'electronics', true),
  createItem('l2', 'lucas', 'Headphones', '🎧', 1, 'electronics', true),
  createItem('l3', 'lucas', 'T-Shirts', '👕', 8, 'clothing'),
  createItem('l4', 'lucas', 'Shorts', '🩳', 5, 'clothing'),
  createItem('l5', 'lucas', 'Light Jacket', '🧥', 1, 'clothing'),
  createItem('l6', 'lucas', 'Raincoat', '🌧️', 1, 'clothing'),
  createItem('l7', 'lucas', 'Pajamas', '🩱', 3, 'clothing'),
  createItem('l8', 'lucas', 'Underwear', '🩲', 10, 'clothing'),
  createItem('l9', 'lucas', 'Hiking Boots', '🥾', 1, 'clothing'),
  createItem('l10', 'lucas', 'Sneakers', '👟', 1, 'clothing'),
  createItem('l11', 'lucas', 'Sunscreen', '☀️', 1, 'toiletries'),
  createItem('l12', 'lucas', 'Book', '📖', 2, 'activities'),
  createItem('l13', 'lucas', 'Sketch Pad', '✏️', 1, 'activities'),
];

export const mockPackingList: PackingList = {
  tripId: mockTrip.id,
  items: mockPackingItems,
  sharedLinks: [],
};

export const categoryLabels: Record<ItemCategory, { label: string; emoji: string }> = {
  clothing: { label: 'Clothing', emoji: '👕' },
  toiletries: { label: 'Toiletries', emoji: '🧴' },
  electronics: { label: 'Electronics', emoji: '📱' },
  documents: { label: 'Documents', emoji: '📄' },
  health: { label: 'Health & Medicine', emoji: '💊' },
  comfort: { label: 'Comfort Items', emoji: '🧸' },
  activities: { label: 'Activities', emoji: '🎮' },
  baby: { label: 'Baby & Toddler', emoji: '👶' },
  misc: { label: 'Miscellaneous', emoji: '📦' },
};

export const kidModeEmojis = ['🎉', '⭐', '🌈', '🎈', '🦋', '🌟', '💫', '🎊'];

export type KidModeLevel = 'little' | 'big' | 'teenager';

export const kidModeLevels: { value: KidModeLevel; label: string; ageRange: string; emoji: string }[] = [
  { value: 'little', label: 'Little Kid', ageRange: '4-7', emoji: '🧒' },
  { value: 'big', label: 'Big Kid', ageRange: '8-11', emoji: '🧑' },
  { value: 'teenager', label: 'Teenager', ageRange: '12+', emoji: '😎' },
];
