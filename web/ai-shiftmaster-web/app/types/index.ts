export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'employee';
  organization_id?: number;
  organization_name?: string;
}

export interface Employee {
  id: number;
  name: string;
  email: string;
  role: string;
  department_id: number;
  department_name?: string;
  availability: AvailabilitySlot[];
  weekly_working_limit: number;
  overtime_limit: number;
  preferences?: EmployeePreferences | null;
  created_at: string;
  updated_at: string;
}

export type ShiftTypeKey = 'morning' | 'day' | 'afternoon' | 'night';

export interface EmployeePreferences {
  preferred_shift?: ShiftTypeKey | null;
  weekly_off_day?: number | null; // 0-6 (Sunday-Saturday)
  work_model?: 'office' | 'remote' | 'hybrid' | null;
}

export interface AvailabilitySlot {
  day: number; // 0-6 (Sunday-Saturday)
  start_time: string;
  end_time: string;
}

export interface Department {
  id: number;
  name: string;
  description?: string;
  created_at: string;
}

export interface Shift {
  id: number;
  employee_id: number;
  employee_name?: string;
  department_id: number;
  department_name?: string;
  start_time: string;
  end_time: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

export interface ShiftRule {
  id: number;
  name: string;
  department_id: number;
  department_name?: string;
  role: string;
  start_time: string;
  end_time: string;
  min_employees: number;
  max_employees: number;
  days_of_week: number[];
  is_active: boolean;
  created_at: string;
}

export interface ShiftConflict {
  type: 'overlap' | 'overtime' | 'availability' | 'understaffed';
  message: string;
  employee_id: number;
  shift_ids: number[];
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  is_read: boolean;
  created_at: string;
}

export interface OptimizationSettings {
  shift_types: ShiftTypeKey[];
  operating_days: string[];
  is_24_7: boolean;
  min_employees_per_shift: number;
  max_employees_per_shift: number;
  max_hours_per_week: number;
  max_consecutive_days: number;
  min_rest_hours: number;
  allow_overtime: boolean;
  consider_preferences: boolean;
  preference_weight: number;
  balance_workload: boolean;
}

export interface OptimizationRequest {
  start_date: string;
  end_date: string;
  department_ids?: number[];
  settings: OptimizationSettings;
}

export interface OptimizedShift extends Shift {
  shift_type: ShiftTypeKey;
  preferred: boolean;
}

export interface OptimizationMetrics {
  coverage: number;
  preference_match: number;
  fairness: number;
  total_hours: number;
  employees_scheduled: number;
}

export interface OptimizationResult {
  shifts: OptimizedShift[];
  conflicts: ShiftConflict[];
  optimization_score: number;
  metrics?: OptimizationMetrics;
  message: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}
