import api from './client';
import type { LeaveRequest, LeaveBalance, LeaveCategory, PublicHoliday } from '../types';

interface TeamCalendarResponse {
  month: number;
  year: number;
  team_members: Array<{
    id: string;
    name: string;
    color: string;
    is_current_user: boolean;
  }>;
  leaves: Array<{
    id: string;
    member_id: string;
    start_date: string;
    end_date: string;
    is_full_day: boolean;
    start_time: string | null;
    end_time: string | null;
    category: string;
    total_hours: number;
  }>;
  holidays: Array<{
    date: string;
    name: string;
  }>;
}

interface TeamCalendarEvent {
  user_name: string;
  user_id: string;
  leave_type: string;
  date: string;
}

/**
 * Leave Management API endpoints
 */
export const leavesApi = {
  // Leave Requests
  getLeaveRequests: async (params?: { status?: string; year?: number }) => {
    const response = await api.get<LeaveRequest[]>('/leaves/requests/my/', { params });
    return response.data;
  },

  // Get pending requests for manager approval
  getPendingApprovals: async () => {
    const response = await api.get<{ results: LeaveRequest[] }>('/leaves/requests/', { params: { status: 'pending', my: 'false' } });
    return response.data.results;
  },

  // Get approval history for manager
  getApprovalHistory: async () => {
    const response = await api.get<{ results: LeaveRequest[] }>('/leaves/requests/', { params: { history: 'true' } });
    return response.data.results;
  },

  getLeaveRequest: async (id: string) => {
    const response = await api.get<LeaveRequest>(`/leaves/requests/${id}/`);
    return response.data;
  },

  createLeaveRequest: async (data: Partial<LeaveRequest> | FormData) => {
    const isFormData = data instanceof FormData;
    const response = await api.post<LeaveRequest>('/leaves/requests/', data, {
      headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : undefined,
    });
    return response.data;
  },

  updateLeaveRequest: async (id: string, data: Partial<LeaveRequest>) => {
    const response = await api.patch<LeaveRequest>(`/leaves/requests/${id}/`, data);
    return response.data;
  },

  deleteLeaveRequest: async (id: string) => {
    const response = await api.delete(`/leaves/requests/${id}/`);
    return response.data;
  },

  approveLeaveRequest: async (id: string, data?: { comment?: string }) => {
    const response = await api.post<LeaveRequest>(`/leaves/requests/${id}/approve/`, data);
    return response.data;
  },

  rejectLeaveRequest: async (id: string, data: { reason: string }) => {
    const response = await api.post<LeaveRequest>(`/leaves/requests/${id}/reject/`, data);
    return response.data;
  },

  cancelLeaveRequest: async (id: string) => {
    const response = await api.post<LeaveRequest>(`/leaves/requests/${id}/cancel/`);
    return response.data;
  },

  // Leave Balances
  getMyLeaveBalance: async (year?: number) => {
    const response = await api.get<LeaveBalance>('/leaves/balances/me/', {
      params: year ? { year } : {},
    });
    return response.data;
  },

  adjustLeaveBalance: async (userId: string, data: { adjusted_hours: number; reason?: string }) => {
    const response = await api.post<LeaveBalance>(`/leaves/balances/${userId}/adjust/`, data);
    return response.data;
  },

  // Leave Categories
  getLeaveCategories: async () => {
    const response = await api.get<LeaveCategory[]>('/leaves/categories/');
    return response.data;
  },

  // Public Holidays
  getPublicHolidays: async (params?: { entity?: string; location?: string; year?: number }) => {
    const response = await api.get<PublicHoliday[]>('/leaves/holidays/', { params });
    return response.data;
  },

  // Team Calendar
  getTeamCalendar: async (params?: { month?: number; year?: number }) => {
    const response = await api.get<TeamCalendarResponse>('/leaves/calendar/', { params });
    return response.data;
  },

  // Reports (HR/Admin)
  getReports: async (params?: { entity?: string; location?: string; department?: string; year?: number }) => {
    const response = await api.get('/leaves/reports/', { params });
    return response.data;
  },
};

export default leavesApi;
