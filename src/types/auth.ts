/**
 * Authentication Types
 * TypeScript interfaces for authentication-related data structures
 */

/**
 * User model matching backend User schema
 */
export interface User {
  id: string;
  email: string;
  fullName?: string;
  avatarUrl?: string;
  createdAt: string;
  updatedAt?: string;
}

/**
 * Authentication state
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * JWT tokens returned from backend
 */
export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}

/**
 * Login response from backend
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Token refresh request
 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/**
 * Backend user response (snake_case)
 */
export interface UserResponse {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at?: string;
}