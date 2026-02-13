/**
 * Trip Types
 * TypeScript interfaces matching backend trip models
 */

export type TravelerType = 'adult' | 'child' | 'infant';

export type ItemCategory = string;

export type WeatherCondition = 'sunny' | 'rainy' | 'cloudy' | 'snowy' | 'mixed';

/**
 * Traveler interfaces
 */
export interface Traveler {
  id: string;
  name: string;
  age: number;
  type: TravelerType;
  avatar?: string;
}

export interface TravelerBase {
  name: string;
  age: number;
  type: TravelerType;
  avatar?: string;
}

/**
 * Weather information
 */
export interface WeatherInfo {
  avgTemp: number;
  tempUnit: 'C' | 'F';
  conditions: WeatherCondition[];
  recommendation: string;
  forecastData?: Record<string, any>;
}

/**
 * Delegation information
 */
export interface DelegationInfo {
  fromPersonId: string;
  fromPersonName: string;
  delegatedAt: string;
}

/**
 * Packing item interfaces
 */
export interface PackingItem {
  id: string;
  personId: string;
  name: string;
  emoji: string;
  quantity: number;
  category: ItemCategory;
  notes?: string;
  isPacked: boolean;
  isEssential: boolean;
  visibleToKid: boolean;
  delegatedTo?: string;
  delegationInfo?: DelegationInfo;
}

export interface PackingItemBase {
  name: string;
  emoji?: string;
  quantity?: number;
  category: ItemCategory;
  notes?: string;
}

/**
 * Packing list organized by person
 */
export interface PackingListForPerson {
  personName: string;
  personId: string;
  items: PackingItem[];
  categories: string[];
}

/**
 * Trip interfaces
 */
export interface Trip {
  id: string;
  userId: string;
  destination: string;
  startDate: string;
  endDate: string;
  activities: string[];
  transport: string[];
  travelers: Traveler[];
  weatherData?: WeatherInfo;
  packingLists: PackingListForPerson[];
  duration: number;
  createdAt: string;
  updatedAt: string;
}

export interface TripBase {
  destination: string;
  startDate: string;
  endDate: string;
  activities?: string[];
  transport?: string[];
}

/**
 * Request/Response types for API
 */
export interface CreateTripRequest {
  destination: string;
  startDate: string;
  endDate: string;
  activities?: string[];
  transport?: string[];
  travelers: TravelerBase[];
}

export interface UpdateTripRequest {
  destination?: string;
  startDate?: string;
  endDate?: string;
  activities?: string[];
  transport?: string[];
  travelers?: TravelerBase[];
}

export interface GenerateTripRequest {
  destination: string;
  startDate: string;
  endDate: string;
  travelers: TravelerBase[];
  activities?: string[];
  transport?: string[];
}

export interface GenerateTripResponse extends Trip {}

export interface TripListResponse {
  trips: Trip[];
  total: number;
}

export type TripGenerationJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface TripGenerationJobResponse {
  jobId: string;
  status: TripGenerationJobStatus;
  tripId?: string | null;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
}

/**
 * Packing item request types
 */
export interface AddItemRequest {
  personId: string;
  name: string;
  category: ItemCategory;
  isEssential?: boolean;
  notes?: string;
  emoji?: string;
  quantity?: number;
}

export interface UpdateItemRequest {
  name?: string;
  category?: ItemCategory;
  isPacked?: boolean;
  isEssential?: boolean;
  notes?: string;
  emoji?: string;
  quantity?: number;
}

export interface DelegateItemRequest {
  fromPersonId: string;
  toPersonId: string;
}

export interface TogglePackedResponse {
  itemId: string;
  isPacked: boolean;
  message: string;
}

/**
 * Trip member management
 */
export interface TripMember {
  userId: string;
  email: string;
  role: 'owner' | 'editor' | 'viewer';
  addedAt: string;
}

export interface AddTripMemberRequest {
  email: string;
  role?: 'editor' | 'viewer';
}