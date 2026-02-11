/**
 * TypeScript types for Google Maps API responses
 */

export interface PlaceSuggestion {
  placeId: string;
  description: string;
  mainText: string;
  secondaryText: string;
}

export interface PlaceDetails {
  placeId: string;
  name: string;
  formattedAddress: string;
  lat: number;
  lng: number;
  types: string[];
}

export interface AutocompleteResponse {
  suggestions: PlaceSuggestion[];
}

export interface PlaceDetailsResponse {
  place: PlaceDetails | null;
}