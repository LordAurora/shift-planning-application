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

// ============================================
// SECURITY AI SERVICES
// ============================================

import {
  SecurityScanRequest,
  SecurityScanResult,
  SecurityRule,
  SecurityRuleRequest,
  TrainingConfig,
  TrainingRun,
  EvaluationResult,
  FeedbackRecord,
  MigrationStatus,
  SecurityDashboardStats,
  Vulnerability,
  EngineRule,
} from '../types';

/**
 * Security Scanning Services - Hybrid Engine (Rule + ML)
 */
export const securityScanService = {
  /**
   * Run a security scan with hybrid detection
   */
  runScan: async (data: {
    content: string;
    filename?: string;
    language?: string;
    detection_mode: 'full' | 'rules_only' | 'critical_only';
  }): Promise<SecurityScanResult> => {
    const response = await apiClient.post<SecurityScanResult>('/security/scans', data);
    return response.data;
  },

  /**
   * Recent persisted scans
   */
  getRecentScans: async (limit = 20): Promise<SecurityScanResult[]> => {
    const response = await apiClient.get<SecurityScanResult[]>('/security/scans', { params: { limit } });
    return response.data;
  },

  /**
   * Rules loaded in the detection engine
   */
  getEngineRules: async (): Promise<EngineRule[]> => {
    const response = await apiClient.get<EngineRule[]>('/security/engine/rules');
    return response.data;
  },

  /**
   * Get scan by ID
   */
  getScan: async (scanId: string): Promise<SecurityScanResult> => {
    const response = await apiClient.get<SecurityScanResult>(`/security/scan/${scanId}`);
    return response.data;
  },

  /**
   * Get all scans with optional filters
   */
  getAllScans: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    scan_type?: string;
  }): Promise<PaginatedResponse<SecurityScanResult>> => {
    const response = await apiClient.get<PaginatedResponse<SecurityScanResult>>('/security/scans', { params });
    return response.data;
  },

  /**
   * Get vulnerabilities with filters
   */
  getVulnerabilities: async (params?: {
    page?: number;
    page_size?: number;
    severity?: string;
    category?: string;
    detection_source?: string;
    false_positive?: boolean;
  }): Promise<PaginatedResponse<Vulnerability>> => {
    const response = await apiClient.get<PaginatedResponse<Vulnerability>>('/security/vulnerabilities', { params });
    return response.data;
  },

  /**
   * Mark vulnerability as false positive
   */
  markFalsePositive: async (vulnId: string, isFalsePositive: boolean): Promise<void> => {
    await apiClient.put(`/security/vulnerabilities/${vulnId}/false-positive`, { is_false_positive: isFalsePositive });
  },

  /**
   * Get dashboard statistics
   */
  getDashboardStats: async (): Promise<SecurityDashboardStats> => {
    const response = await apiClient.get<SecurityDashboardStats>('/security/dashboard/stats');
    return response.data;
  },
};

/**
 * Security Rules Services - Rule-Based Detection Management
 */
export const securityRuleService = {
  /**
   * Get all security rules
   */
  getAll: async (params?: {
    category?: string;
    severity?: string;
    is_active?: boolean;
  }): Promise<SecurityRule[]> => {
    const response = await apiClient.get<SecurityRule[]>('/security/rules', { params });
    return response.data;
  },

  /**
   * Get rule by ID
   */
  getById: async (ruleId: string): Promise<SecurityRule> => {
    const response = await apiClient.get<SecurityRule>(`/security/rules/${ruleId}`);
    return response.data;
  },

  /**
   * Create a new security rule
   */
  create: async (data: SecurityRuleRequest): Promise<SecurityRule> => {
    const response = await apiClient.post<SecurityRule>('/security/rules', data);
    return response.data;
  },

  /**
   * Update an existing rule
   */
  update: async (ruleId: string, data: Partial<SecurityRuleRequest>): Promise<SecurityRule> => {
    const response = await apiClient.put<SecurityRule>(`/security/rules/${ruleId}`, data);
    return response.data;
  },

  /**
   * Delete a rule
   */
  delete: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/security/rules/${ruleId}`);
  },

  /**
   * Toggle rule active status
   */
  toggleActive: async (ruleId: string, isActive: boolean): Promise<void> => {
    await apiClient.put(`/security/rules/${ruleId}/toggle`, { is_active: isActive });
  },

  /**
   * Test a rule pattern against sample code
   */
  testRule: async (pattern: string, patternType: string, sampleCode: string): Promise<{ matches: string[]; count: number }> => {
    const response = await apiClient.post('/security/rules/test', { pattern, pattern_type: patternType, sample_code: sampleCode });
    return response.data;
  },
};

/**
 * Training & Evaluation Services - ML Model Management
 */
export const trainingService = {
  /**
   * Start a new training run
   */
  startTraining: async (config: TrainingConfig): Promise<TrainingRun> => {
    const response = await apiClient.post<TrainingRun>('/security/training/start', config);
    return response.data;
  },

  /**
   * Get training run status
   */
  getTrainingRun: async (runId: string): Promise<TrainingRun> => {
    const response = await apiClient.get<TrainingRun>(`/security/training/runs/${runId}`);
    return response.data;
  },

  /**
   * Get all training runs
   */
  getAllTrainingRuns: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<TrainingRun>> => {
    const response = await apiClient.get<PaginatedResponse<TrainingRun>>('/security/training/runs', { params });
    return response.data;
  },

  /**
   * Cancel a running training
   */
  cancelTraining: async (runId: string): Promise<void> => {
    await apiClient.post(`/security/training/runs/${runId}/cancel`);
  },

  /**
   * Get evaluation results
   */
  getEvaluations: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<EvaluationResult>> => {
    const response = await apiClient.get<PaginatedResponse<EvaluationResult>>('/security/training/evaluations', { params });
    return response.data;
  },

  /**
   * Run model evaluation
   */
  runEvaluation: async (modelVersion: string): Promise<EvaluationResult> => {
    const response = await apiClient.post<EvaluationResult>('/security/training/evaluate', { model_version: modelVersion });
    return response.data;
  },

  /**
   * Get current model metrics
   */
  getCurrentModelMetrics: async (): Promise<{
    version: string;
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_rate: number;
    last_trained: string;
  }> => {
    const response = await apiClient.get('/security/training/current-model');
    return response.data;
  },
};

/**
 * Continuous Learning Services - Feedback & Retraining
 */
export const feedbackService = {
  /**
   * Submit feedback for a vulnerability
   */
  submitFeedback: async (data: {
    vulnerability_id: string;
    feedback_type: 'false_positive' | 'false_negative' | 'correct' | 'severity_change';
    corrected_label?: string;
    notes?: string;
  }): Promise<FeedbackRecord> => {
    const response = await apiClient.post<FeedbackRecord>('/security/feedback', data);
    return response.data;
  },

  /**
   * Get all feedback records
   */
  getAllFeedback: async (params?: {
    page?: number;
    page_size?: number;
    feedback_type?: string;
    used_in_retraining?: boolean;
  }): Promise<PaginatedResponse<FeedbackRecord>> => {
    const response = await apiClient.get<PaginatedResponse<FeedbackRecord>>('/security/feedback', { params });
    return response.data;
  },

  /**
   * Get retraining recommendations
   */
  getRetrainingRecommendation: async (): Promise<{
    should_retrain: boolean;
    reason: string;
    pending_feedback_count: number;
    accuracy_drift: number;
    recommended_config?: TrainingConfig;
  }> => {
    const response = await apiClient.get('/security/feedback/retraining-recommendation');
    return response.data;
  },
};

/**
 * Migration Services - Huawei Cloud / MindSpore
 */
export const migrationService = {
  /**
   * Get current migration status
   */
  getStatus: async (): Promise<MigrationStatus> => {
    const response = await apiClient.get<MigrationStatus>('/security/migration/status');
    return response.data;
  },

  /**
   * Get migration checklist
   */
  getChecklist: async (): Promise<{
    items: {
      id: string;
      title: string;
      description: string;
      status: 'pending' | 'completed' | 'blocked';
      category: 'dataset' | 'model' | 'training' | 'inference' | 'infrastructure';
    }[];
    completed_count: number;
    total_count: number;
  }> => {
    const response = await apiClient.get('/security/migration/checklist');
    return response.data;
  },

  /**
   * Validate MindSpore compatibility
   */
  validateCompatibility: async (): Promise<{
    is_compatible: boolean;
    issues: {
      component: string;
      issue: string;
      severity: 'warning' | 'error';
      suggestion: string;
    }[];
  }> => {
    const response = await apiClient.get('/security/migration/validate');
    return response.data;
  },

  /**
   * Export model for MindSpore
   */
  exportForMindSpore: async (modelVersion: string): Promise<{
    export_path: string;
    format: string;
    size_bytes: number;
  }> => {
    const response = await apiClient.post('/security/migration/export', { model_version: modelVersion });
    return response.data;
  },
};
