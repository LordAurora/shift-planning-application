import apiClient from './api';
import { 
  LoginRequest, 
  LoginResponse, 
  Employee, 
  Department, 
  Shift, 
  ShiftRule, 
  Notification,
  OptimizationRequest,
  OptimizationResult,
  PaginatedResponse,
  ApiResponse 
} from '../types';

// Auth Services
export const authService = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', data);
    return response.data;
  },
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },
  refreshToken: async (): Promise<{ access_token: string }> => {
    const response = await apiClient.post('/auth/refresh');
    return response.data;
  },
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
  register: async (data: { name: string; email: string; password: string }) => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },
};

// Employee Services
export const employeeService = {
  getAll: async (params?: { page?: number; page_size?: number; department_id?: number; search?: string }): Promise<PaginatedResponse<Employee>> => {
    const response = await apiClient.get<PaginatedResponse<Employee>>('/employees', { params });
    return response.data;
  },
  getById: async (id: number): Promise<Employee> => {
    const response = await apiClient.get<Employee>(`/employees/${id}`);
    return response.data;
  },
  create: async (data: Partial<Employee>): Promise<Employee> => {
    const response = await apiClient.post<Employee>('/employees', data);
    return response.data;
  },
  update: async (id: number, data: Partial<Employee>): Promise<Employee> => {
    const response = await apiClient.put<Employee>(`/employees/${id}`, data);
    return response.data;
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/employees/${id}`);
  },
};

// Department Services
export const departmentService = {
  getAll: async (): Promise<Department[]> => {
    const response = await apiClient.get<Department[]>('/departments');
    return response.data;
  },
  getById: async (id: number): Promise<Department> => {
    const response = await apiClient.get<Department>(`/departments/${id}`);
    return response.data;
  },
  create: async (data: Partial<Department>): Promise<Department> => {
    const response = await apiClient.post<Department>('/departments', data);
    return response.data;
  },
  update: async (id: number, data: Partial<Department>): Promise<Department> => {
    const response = await apiClient.put<Department>(`/departments/${id}`, data);
    return response.data;
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/departments/${id}`);
  },
};

// Shift Services
export const shiftService = {
  getAll: async (params?: { 
    page?: number; 
    page_size?: number; 
    start_date?: string; 
    end_date?: string;
    employee_id?: number;
    department_id?: number;
  }): Promise<PaginatedResponse<Shift>> => {
    const response = await apiClient.get<PaginatedResponse<Shift>>('/shifts', { params });
    return response.data;
  },
  getById: async (id: number): Promise<Shift> => {
    const response = await apiClient.get<Shift>(`/shifts/${id}`);
    return response.data;
  },
  create: async (data: Partial<Shift>): Promise<Shift> => {
    const response = await apiClient.post<Shift>('/shifts', data);
    return response.data;
  },
  update: async (id: number, data: Partial<Shift>): Promise<Shift> => {
    const response = await apiClient.put<Shift>(`/shifts/${id}`, data);
    return response.data;
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/shifts/${id}`);
  },
  getConflicts: async (params: { start_date: string; end_date: string }) => {
    const response = await apiClient.get('/shifts/conflicts', { params });
    return response.data;
  },
  createBulk: async (shifts: Array<{
    employee_id: number;
    department_id: number;
    start_time: string;
    end_time: string;
    status: string;
  }>): Promise<{ created_count: number; failed_count: number; message: string }> => {
    const response = await apiClient.post('/shifts/bulk', { shifts });
    return response.data;
  },
};

// Shift Rules Services
export const shiftRuleService = {
  getAll: async (params?: { department_id?: number; is_active?: boolean }): Promise<ShiftRule[]> => {
    const response = await apiClient.get<ShiftRule[]>('/rules', { params });
    return response.data;
  },
  getById: async (id: number): Promise<ShiftRule> => {
    const response = await apiClient.get<ShiftRule>(`/rules/${id}`);
    return response.data;
  },
  create: async (data: Partial<ShiftRule>): Promise<ShiftRule> => {
    const response = await apiClient.post<ShiftRule>('/rules', data);
    return response.data;
  },
  update: async (id: number, data: Partial<ShiftRule>): Promise<ShiftRule> => {
    const response = await apiClient.put<ShiftRule>(`/rules/${id}`, data);
    return response.data;
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/rules/${id}`);
  },
};

// AI Optimization Services
export const aiService = {
  optimize: async (data: OptimizationRequest): Promise<OptimizationResult> => {
    const response = await apiClient.post<OptimizationResult>('/ai/optimize', data);
    return response.data;
  },
  applyOptimization: async (shifts: Shift[]): Promise<{ message: string; created_count: number }> => {
    const response = await apiClient.post('/ai/apply', { shifts }, { timeout: 120000 });
    return response.data;
  },
};

// Dashboard Services
export interface DashboardSummary {
  period: { start_date: string; end_date: string };
  total_employees: number;
  total_departments: number;
  total_shifts: number;
  total_hours: number;
  employees_scheduled: number;
  over_contract: number;
  cancelled_shifts: number;
  by_weekday: { name: string; shifts: number; hours: number; employees: number }[];
  shift_types: { name: string; value: number }[];
  departments: { name: string; value: number }[];
  monthly_trend: { month: string; scheduled: number; completed: number; cancelled: number }[];
  upcoming_shifts: {
    id: number;
    employee: string | null;
    department: string | null;
    start_time: string;
    end_time: string;
    status: string;
  }[];
}

export const dashboardService = {
  getSummary: async (params: { start_date: string; end_date: string }): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/dashboard/summary', { params });
    return response.data;
  },
};

// Notification Services
export const notificationService = {
  getAll: async (params?: { is_read?: boolean }): Promise<Notification[]> => {
    const response = await apiClient.get<Notification[]>('/notifications', { params });
    return response.data;
  },
  markAsRead: async (id: number): Promise<void> => {
    await apiClient.put(`/notifications/${id}/read`);
  },
  markAllAsRead: async (): Promise<void> => {
    await apiClient.put('/notifications/read-all');
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/notifications/${id}`);
  },
};
