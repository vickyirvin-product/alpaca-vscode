/**
 * API Client Configuration
 * Centralized API client for making requests to the backend
 */

import { 
  User, 
  UserResponse, 
  AuthTokens, 
  LoginResponse, 
  RefreshTokenRequest 
} from '@/types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Data Transformation Utilities
 */

/**
 * Convert snake_case to camelCase
 */
function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert camelCase to snake_case
 */
function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Recursively transform object keys from snake_case to camelCase
 */
export function transformToCamelCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj;
  
  if (Array.isArray(obj)) {
    return obj.map(item => transformToCamelCase(item)) as T;
  }
  
  if (typeof obj === 'object' && obj.constructor === Object) {
    return Object.keys(obj).reduce((acc, key) => {
      const camelKey = toCamelCase(key);
      acc[camelKey] = transformToCamelCase(obj[key]);
      return acc;
    }, {} as any) as T;
  }
  
  return obj;
}

/**
 * Recursively transform object keys from camelCase to snake_case
 */
export function transformToSnakeCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj;
  
  if (Array.isArray(obj)) {
    return obj.map(item => transformToSnakeCase(item)) as T;
  }
  
  if (typeof obj === 'object' && obj.constructor === Object) {
    return Object.keys(obj).reduce((acc, key) => {
      const snakeKey = toSnakeCase(key);
      acc[snakeKey] = transformToSnakeCase(obj[key]);
      return acc;
    }, {} as any) as T;
  }
  
  return obj;
}

/**
 * Token Management
 */

export const tokenManager = {
  getAccessToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
  },
  
  setAccessToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
  },
  
  getRefreshToken: (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  
  setRefreshToken: (token: string): void => {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },
  
  setTokens: (tokens: AuthTokens): void => {
    localStorage.setItem(TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  },
  
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
  
  hasValidToken: (): boolean => {
    return !!localStorage.getItem(TOKEN_KEY);
  }
};

/**
 * Token refresh logic
 */
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenManager.getRefreshToken();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (!response.ok) {
      throw new Error('Token refresh failed');
    }
    
    const data: LoginResponse = await response.json();
    const tokens: AuthTokens = {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      tokenType: data.token_type,
    };
    
    tokenManager.setTokens(tokens);
    return tokens.accessToken;
  } catch (error) {
    tokenManager.clearTokens();
    window.location.href = '/login';
    throw error;
  }
}

/**
 * Base fetch wrapper with error handling and interceptors
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Request interceptor: Add auth token
  const token = tokenManager.getAccessToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // Include cookies for authentication
  };

  try {
    const response = await fetch(url, config);

    // Response interceptor: Handle 401 errors
    if (response.status === 401) {
      if (!isRefreshing) {
        isRefreshing = true;
        
        try {
          const newToken = await refreshAccessToken();
          isRefreshing = false;
          onTokenRefreshed(newToken);
          
          // Retry original request with new token
          config.headers = {
            ...config.headers,
            'Authorization': `Bearer ${newToken}`,
          };
          
          const retryResponse = await fetch(url, config);
          
          if (!retryResponse.ok) {
            const errorData = await retryResponse.json().catch(() => ({}));
            throw new Error(
              errorData.detail || `API Error: ${retryResponse.status} ${retryResponse.statusText}`
            );
          }
          
          const data = await retryResponse.json();
          return transformToCamelCase<T>(data);
        } catch (refreshError) {
          isRefreshing = false;
          throw refreshError;
        }
      } else {
        // Wait for token refresh to complete
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh(async (newToken: string) => {
            try {
              config.headers = {
                ...config.headers,
                'Authorization': `Bearer ${newToken}`,
              };
              
              const retryResponse = await fetch(url, config);
              
              if (!retryResponse.ok) {
                const errorData = await retryResponse.json().catch(() => ({}));
                throw new Error(
                  errorData.detail || `API Error: ${retryResponse.status} ${retryResponse.statusText}`
                );
              }
              
              const data = await retryResponse.json();
              resolve(transformToCamelCase<T>(data));
            } catch (error) {
              reject(error);
            }
          });
        });
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    // Transform response from snake_case to camelCase
    return transformToCamelCase<T>(data);
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
}

/**
 * API Client Methods
 */
export const api = {
  /**
   * GET request
   */
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiFetch<T>(endpoint, { ...options, method: 'GET' }),

  /**
   * POST request
   */
  post: <T>(endpoint: string, data?: unknown, options?: RequestInit) => {
    // Transform request data from camelCase to snake_case
    const transformedData = data ? transformToSnakeCase(data) : undefined;
    return apiFetch<T>(endpoint, {
      ...options,
      method: 'POST',
      body: transformedData ? JSON.stringify(transformedData) : undefined,
    });
  },

  /**
   * PUT request
   */
  put: <T>(endpoint: string, data?: unknown, options?: RequestInit) => {
    // Transform request data from camelCase to snake_case
    const transformedData = data ? transformToSnakeCase(data) : undefined;
    return apiFetch<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: transformedData ? JSON.stringify(transformedData) : undefined,
    });
  },

  /**
   * PATCH request
   */
  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit) => {
    // Transform request data from camelCase to snake_case
    const transformedData = data ? transformToSnakeCase(data) : undefined;
    return apiFetch<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: transformedData ? JSON.stringify(transformedData) : undefined,
    });
  },

  /**
   * DELETE request
   */
  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiFetch<T>(endpoint, { ...options, method: 'DELETE' }),
};

/**
 * Authentication API Methods
 */
export const authApi = {
  /**
   * Initiate Google OAuth login flow
   * Redirects to backend which then redirects to Google
   */
  loginWithGoogle: (): void => {
    window.location.href = `${API_BASE_URL}/auth/login/google`;
  },

  /**
   * Handle OAuth callback
   * This should be called from the callback route
   */
  handleAuthCallback: async (): Promise<AuthTokens> => {
    // The backend callback endpoint returns tokens directly
    // We need to extract them from the current URL or make a request
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (!code) {
      throw new Error('No authorization code found in callback');
    }

    // The backend handles the callback and returns tokens
    // We'll fetch from the callback endpoint
    const response = await fetch(`${API_BASE_URL}/auth/callback/google${window.location.search}`, {
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Authentication callback failed');
    }

    const data: LoginResponse = await response.json();
    const tokens: AuthTokens = {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      tokenType: data.token_type,
    };

    tokenManager.setTokens(tokens);
    return tokens;
  },

  /**
   * Logout user
   * Clears tokens and redirects to login
   */
  logout: async (): Promise<void> => {
    try {
      // Call backend logout endpoint if it exists
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      tokenManager.clearTokens();
    }
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const userData = await api.get<UserResponse>('/auth/users/me');
    // Transform is already done by api.get, but ensure proper typing
    return userData as unknown as User;
  },

  /**
   * Verify token validity
   */
  verifyToken: async (): Promise<boolean> => {
    try {
      await authApi.getCurrentUser();
      return true;
    } catch (error) {
      return false;
    }
  },

  /**
   * Refresh access token
   */
  refreshToken: async (): Promise<AuthTokens> => {
    const newToken = await refreshAccessToken();
    return {
      accessToken: newToken,
      refreshToken: tokenManager.getRefreshToken() || '',
      tokenType: 'bearer',
    };
  },
};

/**
 * Health check endpoint
 */
export const checkHealth = () => api.get<{ status: string }>('/healthz');

/**
 * Get API base URL (useful for debugging)
 */
export const getApiBaseUrl = () => API_BASE_URL;
/**
 * Trip API Methods
 */
import {
  Trip,
  TripListResponse,
  CreateTripRequest,
  UpdateTripRequest,
  GenerateTripRequest,
  GenerateTripResponse,
  AddItemRequest,
  UpdateItemRequest,
  PackingItem,
  TogglePackedResponse,
} from '@/types/trip';

export const tripApi = {
  /**
   * Create a new trip with AI-generated packing lists
   */
  createTrip: async (data: CreateTripRequest): Promise<Trip> => {
    return api.post<Trip>('/api/v1/trips', data);
  },

  /**
   * Generate a trip using AI (same as createTrip but explicit naming)
   */
  generateTrip: async (data: GenerateTripRequest): Promise<GenerateTripResponse> => {
    return api.post<GenerateTripResponse>('/api/v1/trips', data);
  },

  /**
   * Get all trips for the current user
   */
  getTrips: async (): Promise<TripListResponse> => {
    return api.get<TripListResponse>('/api/v1/trips');
  },

  /**
   * Get a specific trip by ID
   */
  getTrip: async (tripId: string): Promise<Trip> => {
    return api.get<Trip>(`/api/v1/trips/${tripId}`);
  },

  /**
   * Update an existing trip
   */
  updateTrip: async (tripId: string, data: UpdateTripRequest): Promise<Trip> => {
    return api.put<Trip>(`/api/v1/trips/${tripId}`, data);
  },

  /**
   * Delete a trip
   */
  deleteTrip: async (tripId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/trips/${tripId}`);
  },

  /**
   * Add a packing item to a trip
   */
  addPackingItem: async (tripId: string, data: AddItemRequest): Promise<PackingItem> => {
    return api.post<PackingItem>(`/api/v1/packing/${tripId}/items`, data);
  },

  /**
   * Update a packing item
   */
  updatePackingItem: async (
    tripId: string,
    itemId: string,
    data: UpdateItemRequest
  ): Promise<PackingItem> => {
    return api.put<PackingItem>(`/api/v1/packing/${tripId}/items/${itemId}`, data);
  },

  /**
   * Toggle packed status of an item
   */
  togglePackedStatus: async (
    tripId: string,
    itemId: string
  ): Promise<TogglePackedResponse> => {
    return api.put<TogglePackedResponse>(
      `/api/v1/packing/${tripId}/items/${itemId}/toggle-packed`
    );
  },

  /**
   * Delete a packing item
   */
  deletePackingItem: async (tripId: string, itemId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/packing/${tripId}/items/${itemId}`);
  },

  /**
   * Add a member to a trip (for future collaboration features)
   */
  addTripMember: async (tripId: string, email: string): Promise<void> => {
    return api.post<void>(`/api/v1/trips/${tripId}/members`, { email });
  },

  /**
   * Remove a member from a trip (for future collaboration features)
   */
  removeTripMember: async (tripId: string, userId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/trips/${tripId}/members/${userId}`);
  },
};

/**
 * Packing List API Methods
 */
export const packingApi = {
  /**
   * Toggle packed status of an item
   */
  toggleItemPacked: async (tripId: string, itemId: string): Promise<TogglePackedResponse> => {
    return api.patch<TogglePackedResponse>(`/api/v1/trips/${tripId}/items/${itemId}/toggle-packed`);
  },

  /**
   * Add a packing item to a trip
   */
  addPackingItem: async (tripId: string, data: AddItemRequest): Promise<PackingItem> => {
    return api.post<PackingItem>(`/api/v1/trips/${tripId}/items`, data);
  },

  /**
   * Update a packing item
   */
  updatePackingItem: async (
    tripId: string,
    itemId: string,
    data: UpdateItemRequest
  ): Promise<PackingItem> => {
    return api.put<PackingItem>(`/api/v1/trips/${tripId}/items/${itemId}`, data);
  },

  /**
   * Delete a packing item
   */
  deletePackingItem: async (tripId: string, itemId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/trips/${tripId}/items/${itemId}`);
  },

  /**
   * Delegate an item to another person
   */
  delegateItem: async (
    tripId: string,
    itemId: string,
    fromPersonId: string,
    toPersonId: string
  ): Promise<PackingItem> => {
    return api.post<PackingItem>(`/api/v1/trips/${tripId}/items/${itemId}/delegate`, {
      fromPersonId,
      toPersonId,
    });
  },

  /**
   * Add a category to a person's packing list
   */
  addCategory: async (tripId: string, personId: string, categoryName: string): Promise<{ message: string; category: string }> => {
    return api.post<{ message: string; category: string }>(`/api/v1/trips/${tripId}/categories`, {
      personId,
      categoryName,
    });
  },

  /**
   * Delete a category from a person's packing list
   */
  deleteCategory: async (tripId: string, category: string): Promise<void> => {
    return api.delete<void>(`/api/v1/trips/${tripId}/categories/${category}`);
  },
};

/**
 * Collaboration API Methods
 */
export interface NudgeRequest {
  personId: string;
  message?: string;
}

export interface NudgeResponse {
  id: string;
  tripId: string;
  fromUserId: string;
  toUserEmail: string;
  message?: string;
  isRead: boolean;
  createdAt: string;
  tripDestination: string;
  tripStartDate: string;
  fromUserName?: string;
}

export const collaborationApi = {
  /**
   * Send a nudge to a person to remind them to pack
   */
  sendNudge: async (tripId: string, personId: string, message?: string): Promise<NudgeResponse> => {
    return api.post<NudgeResponse>(`/api/v1/trips/${tripId}/nudges`, {
      personId,
      message,
    });
  },

  /**
   * Get nudges for the current user
   */
  getNudges: async (unreadOnly: boolean = false): Promise<NudgeResponse[]> => {
    const query = unreadOnly ? '?unread_only=true' : '';
    return api.get<NudgeResponse[]>(`/api/v1/nudges${query}`);
  },

  /**
   * Mark a nudge as read
   */
  markNudgeRead: async (nudgeId: string): Promise<NudgeResponse> => {
    return api.put<NudgeResponse>(`/api/v1/nudges/${nudgeId}/mark-read`);
  },

  /**
   * Generate a share link for a trip
   */
  generateShareLink: async (
    tripId: string,
    expirationDays?: number
  ): Promise<{ shareUrl: string; shareToken: string; expiresAt?: string }> => {
    return api.post<{ shareUrl: string; shareToken: string; expiresAt?: string }>(
      `/api/v1/trips/${tripId}/share`,
      { expirationDays }
    );
  },

  /**
   * Revoke share access for a trip
   */
  revokeShareLink: async (tripId: string): Promise<void> => {
    return api.delete<void>(`/api/v1/trips/${tripId}/share`);
  },
};

/**
 * Maps API Methods
 */
import { AutocompleteResponse, PlaceDetailsResponse } from '@/types/maps';

export const mapsApi = {
  /**
   * Get location autocomplete suggestions
   */
  getAutocompleteSuggestions: async (input: string): Promise<AutocompleteResponse> => {
    return api.get<AutocompleteResponse>(`/api/v1/maps/autocomplete?input=${encodeURIComponent(input)}`);
  },

  /**
   * Get place details by place ID
   */
  getPlaceDetails: async (placeId: string): Promise<PlaceDetailsResponse> => {
    return api.get<PlaceDetailsResponse>(`/api/v1/maps/place/${placeId}`);
  },
};

/**
 * Weather API Methods
 */
export interface WeatherForecastResponse {
  avgTemp: number;
  tempUnit: string;
  conditions: string[];
  recommendation: string;
  forecastData?: {
    location: string;
    country: string;
    dailyForecasts: Array<{
      date: string;
      maxTempC: number;
      minTempC: number;
      avgTempC: number;
      condition: string;
      chanceOfRain: number;
      chanceOfSnow: number;
    }>;
  };
}

export const weatherApi = {
  /**
   * Get weather forecast for a location and date range (public endpoint)
   * This endpoint does not require authentication, so we explicitly exclude auth headers
   */
  getForecast: async (
    location: string,
    startDate: string,
    endDate: string
  ): Promise<WeatherForecastResponse> => {
    const url = `${API_BASE_URL}/api/v1/weather/forecast?location=${encodeURIComponent(location)}&start_date=${startDate}&end_date=${endDate}`;
    
    // Make request without authentication headers for public endpoint
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Weather API Error: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    return transformToCamelCase<WeatherForecastResponse>(data);
  },
};

/**
 * LLM API Methods
 */
export interface GeneratePackingListRequest {
  destination: string;
  startDate: string;
  endDate: string;
  activities: string[];
  transport?: string[];
  weather: any;
  travelers: any[];
}

export const llmApi = {
  /**
   * Generate context-aware packing list using LLM
   */
  generatePackingList: async (data: GeneratePackingListRequest): Promise<PackingItem[]> => {
    return api.post<PackingItem[]>('/api/v1/llm/generate-packing-list', data);
  },
};