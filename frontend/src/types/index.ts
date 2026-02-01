/**
 * Type definitions for Leave Management System
 */

export interface User {
  id: string;
  email: string;
  role: 'EMPLOYEE' | 'MANAGER' | 'HR' | 'ADMIN';
  status: 'ACTIVE' | 'INACTIVE';
  entity?: string;
  location?: string;
  department?: string;
  department_name?: string;
  entity_name?: string;
  location_name?: string;
  join_date?: string;
  avatar_url?: string;
  first_name?: string;
  last_name?: string;
  has_completed_onboarding?: boolean;
}

export interface Entity {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface Location {
  id: string;
  entity: string;
  name: string;
  city: string;
  state?: string;
  country: string;
  timezone: string;
  is_active: boolean;
}

export interface Department {
  id: string;
  entity: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface LeaveCategory {
  id: string;
  name: string;
  code: string;
  color: string;
  requires_document: boolean;
  sort_order: number;
  is_active: boolean;
}

export interface LeaveBalance {
  id: string;
  user: string;
  year: number;
  allocated_hours: number;
  used_hours: number;
  adjusted_hours: number;
  remaining_hours: number;
  remaining_days?: number;
}

export type ShiftType = 'FULL_DAY' | 'CUSTOM_HOURS';
export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';

export interface LeaveRequest {
  id: string;
  user: string;
  user_name?: string;
  user_email?: string;
  user_timezone?: string; // GMT offset label e.g., "GMT+9"
  user_location_name?: string;
  department_name?: string;
  leave_category?: LeaveCategory | string;
  category?: LeaveCategory; // Populated by serializer
  start_date: string;
  end_date: string;
  shift_type: ShiftType;
  start_time?: string;
  end_time?: string;
  total_hours: number;
  reason: string;
  attachment_url?: string;
  status: LeaveStatus;
  approved_by?: string;
  approved_by_name?: string;
  approved_at?: string;
  rejection_reason?: string;
  approver_comment?: string;
  created_at: string;
  updated_at: string;
}

export interface PublicHoliday {
  id: string;
  entity?: string;
  location?: string;
  name: string;
  date: string;
  is_recurring: boolean;
  year: number;
  is_active: boolean;
}

export interface Notification {
  id: string;
  user: string;
  type: string;
  title: string;
  message: string;
  link?: string;
  is_read: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  entity: string;
  location: string;
  department: string;
}

// Business Trip types (separate from leaves, no approval workflow, no balance impact)
export interface BusinessTrip {
  id: string;
  user: string;
  user_name?: string;
  user_email?: string;
  city: string;
  country: string;
  start_date: string;
  end_date: string;
  note: string;
  attachment_url?: string;
  created_at: string;
  updated_at: string;
}

export interface BusinessTripCreate {
  start_date: string;
  end_date: string;
  city: string;     // Required field
  country: string;  // Required field
  note?: string;    // Optional note
  attachment_url?: string;
}

// Business trip data for calendar
export interface BusinessTripCalendar {
  id: string;
  member_id: string;
  start_date: string;
  end_date: string;
  city: string;
  country: string;
  note: string;
}
