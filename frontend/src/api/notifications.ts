import api from './client';
import type { Notification } from '../types';

/**
 * Notifications API endpoints
 */
export const notificationsApi = {
  /**
   * Get user notifications
   */
  getNotifications: async (params?: { read?: boolean }) => {
    const response = await api.get<Notification[]>('/notifications/', { params });
    return response.data;
  },

  /**
   * Mark notification as read
   */
  markAsRead: async (id: string) => {
    const response = await api.post<Notification>(`/notifications/${id}/`);
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async () => {
    const response = await api.post('/notifications/mark-all-read/');
    return response.data;
  },

  /**
   * Get unread count
   */
  getUnreadCount: async () => {
    const response = await api.get<{ count: number }>('/notifications/unread-count/');
    return response.data;
  },
};

export default notificationsApi;
