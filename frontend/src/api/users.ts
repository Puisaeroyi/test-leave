import api from './client';
import type { Entity, Location, Department, User } from '../types';

/**
 * HR/Admin API endpoints
 */
export const hrApi = {
  // List users with filters (HR/Admin)
  getUsers: async (params?: { role?: string; department?: string; status?: string }) => {
    const response = await api.get<User[]>('/users/', { params });
    return response.data;
  },

  // Get user detail
  getUser: async (id: string) => {
    const response = await api.get<User>(`/users/${id}/`);
    return response.data;
  },

  // Create new user (HR/Admin)
  createUser: async (data: {
    email: string;
    password?: string;
    first_name?: string;
    last_name?: string;
    role?: string;
  }) => {
    const response = await api.post<User>('/users/create/', data);
    return response.data;
  },

  // Setup user (HR/Admin)
  setupUser: async (id: string, data: {
    department_id: string;
    role?: string;
    join_date?: string;
    allocated_hours?: number;
  }) => {
    const response = await api.post<{
      user: User;
      balance: { year: number; allocated_hours: number; remaining_hours: number };
    }>(`/users/${id}/setup/`, data);
    return response.data;
  },

  // Adjust leave balance (HR/Admin)
  adjustBalance: async (userId: string, data: {
    year?: number;
    allocated_hours?: number;
    adjustment_hours?: number;
    reason: string;
  }) => {
    const response = await api.post<{
      id: string;
      year: number;
      allocated_hours: number;
      used_hours: number;
      adjusted_hours: number;
      remaining_hours: number;
    }>(`/users/${userId}/balance/adjust/`, data);
    return response.data;
  },

  // Entities
  getEntities: async () => {
    const response = await api.get<Entity[]>('/organizations/entities/');
    return response.data;
  },

  // Locations
  getLocations: async (entityId?: string) => {
    const response = await api.get<Location[]>('/organizations/locations/', {
      params: entityId ? { entity: entityId } : {},
    });
    return response.data;
  },

  // Departments
  getDepartments: async (entityId?: string) => {
    const response = await api.get<Department[]>('/organizations/departments/', {
      params: entityId ? { entity: entityId } : {},
    });
    return response.data;
  },
};

export default hrApi;
