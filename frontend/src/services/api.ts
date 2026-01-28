/**
 * API service for backend communication
 */

// Use env variable, or dynamically detect hostname for network access
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000/api/v1`;

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('access_token');

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Calendar API
  async getTeamCalendar(month: number, year: number, memberIds?: string[]) {
    const params = new URLSearchParams({
      month: month.toString(),
      year: year.toString(),
    });

    if (memberIds && memberIds.length > 0) {
      memberIds.forEach(id => params.append('member_ids', id));
    }

    return this.request(`/leaves/calendar/?${params.toString()}`);
  }

  // Notifications API
  async getNotifications(page = 1, pageSize = 20, isRead?: boolean) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (isRead !== undefined) {
      params.append('is_read', isRead.toString());
    }

    return this.request(`/notifications/?${params.toString()}`);
  }

  async markNotificationRead(notificationId: string) {
    return this.request(`/notifications/${notificationId}/`, {
      method: 'POST',
    });
  }

  async markAllNotificationsRead() {
    return this.request('/notifications/mark-all-read/', {
      method: 'POST',
    });
  }

  async getUnreadCount() {
    return this.request('/notifications/unread-count/');
  }
}

export const apiService = new ApiService();
