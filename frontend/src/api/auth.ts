import api from './client';
import type { AuthTokens, LoginRequest, RegisterRequest, User } from '../types';

/**
 * Authentication API endpoints
 */
export const authApi = {
  /**
   * Register new user (includes onboarding data)
   */
  register: async (data: RegisterRequest) => {
    const response = await api.post<{ user: User & { tokens: AuthTokens } }>('/auth/register/', data);
    return response.data;
  },

  /**
   * Login user
   */
  login: async (data: LoginRequest) => {
    const response = await api.post<{ user: User & { tokens: AuthTokens } }>('/auth/login/', data);
    return response.data;
  },

  /**
   * Logout user (blacklist refresh token)
   */
  logout: async (refreshToken: string) => {
    const response = await api.post('/auth/logout/', { refresh: refreshToken });
    return response.data;
  },

  /**
   * Get current user info
   */
  me: async () => {
    const response = await api.get<User>('/auth/me/');
    return response.data;
  },
};

export default authApi;
