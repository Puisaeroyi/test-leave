import api from './client';

export interface Entity {
  id: string;
  entity_name: string;
  code: string;
  is_active: boolean;
}

export interface Location {
  id: string;
  entity: string;
  location_name: string;
  city: string;
  country: string;
  is_active: boolean;
}

export interface Department {
  id: string;
  entity: string;
  location?: string | null;
  department_name: string;
  code: string;
  is_active: boolean;
}

/**
 * Organization API endpoints
 */
export const organizationsApi = {
  /**
   * Get all entities
   */
  getEntities: async () => {
    const response = await api.get<Entity[]>('/organizations/entities/');
    return response.data;
  },

  /**
   * Get locations (optionally filtered by entity)
   */
  getLocations: async (entityId?: string) => {
    const params = entityId ? { entity_id: entityId } : {};
    const response = await api.get<Location[]>('/organizations/locations/', { params });
    return response.data;
  },

  /**
   * Get departments (optionally filtered by entity or location)
   * If locationId is provided, it takes precedence over entityId for filtering
   */
  getDepartments: async (entityId?: string, locationId?: string) => {
    const params: Record<string, string> = {};
    if (locationId) {
      params.location_id = locationId;
    } else if (entityId) {
      params.entity_id = entityId;
    }
    const response = await api.get<Department[]>('/organizations/departments/', { params });
    return response.data;
  },
};

export default organizationsApi;
