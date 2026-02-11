export interface TripInfo {
  id: string;
  destination: string;
  startDate: string;
  endDate: string;
  duration: number;
  weather: WeatherInfo;
  travelers: Traveler[];
  createdAt: string;
  activities?: string[];
}

export interface WeatherInfo {
  avgTemp: number;
  tempUnit: 'C' | 'F';
  conditions: ('sunny' | 'rainy' | 'cloudy' | 'snowy' | 'mixed')[];
  recommendation: string;
}

export interface Traveler {
  id: string;
  name: string;
  age: number;
  type: 'adult' | 'child' | 'infant';
  avatar?: string;
}

export interface DelegationInfo {
  fromPersonId: string;
  fromPersonName: string;
  delegatedAt: string;
}

export interface PackingItem {
  id: string;
  visibleToKid: boolean;
  personId: string;
  name: string;
  emoji: string;
  quantity: number;
  category: ItemCategory;
  isPacked: boolean;
  isEssential: boolean;
  delegatedTo?: string;
  delegationInfo?: DelegationInfo;
  notes?: string;
}

export type ItemCategory = 
  | 'clothing'
  | 'toiletries'
  | 'electronics'
  | 'documents'
  | 'health'
  | 'comfort'
  | 'activities'
  | 'baby'
  | 'misc';

export interface PackingList {
  tripId: string;
  items: PackingItem[];
  sharedLinks: SharedLink[];
}

export interface SharedLink {
  id: string;
  recipientName: string;
  itemIds: string[];
  createdAt: string;
  completedAt?: string;
  url: string;
}

export interface Crew {
  id: string;
  name: string;
  members: Traveler[];
  createdAt: string;
}
