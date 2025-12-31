/**
 * Type utilities for API responses.
 * These types work with the OpenAPI-generated types.
 */

// API Response wrapper type
export interface ApiResponse<T> {
  data: T;
  status: number;
  ok: boolean;
}

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

// Error response type
export interface ApiError {
  detail: string;
  status_code?: number;
}

