export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name?: string;
  roles: string[];
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  organization_id: string;
  roles: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    request_id?: string;
  };
  timestamp: string;
}

