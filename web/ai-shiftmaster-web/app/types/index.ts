export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'employee';
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
  created_at: string;
  updated_at: string;
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
  type: 'overlap' | 'overtime' | 'availability';
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

export interface OptimizationRequest {
  start_date: string;
  end_date: string;
  department_ids?: number[];
}

export interface OptimizationResult {
  shifts: Shift[];
  conflicts: ShiftConflict[];
  optimization_score: number;
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

// ============================================
// SECURITY AI MODULE TYPES
// ============================================

/**
 * Severity levels aligned with CWE/OWASP
 */
export type VulnerabilitySeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

/**
 * Detection source in hybrid engine
 */
export type DetectionSource = 'rule' | 'ml' | 'hybrid';

/**
 * Vulnerability category (CWE-aligned)
 */
export type VulnerabilityCategory =
  | 'sql_injection'
  | 'command_injection'
  | 'path_traversal'
  | 'xss'
  | 'hardcoded_secret'
  | 'weak_crypto'
  | 'auth_bypass'
  | 'insecure_config'
  | 'access_control'
  | 'data_exposure'
  | 'other';

/**
 * Single vulnerability finding
 */
export interface Vulnerability {
  id: string;
  category: VulnerabilityCategory;
  severity: VulnerabilitySeverity;
  title: string;
  description: string;
  file_path?: string;
  line_number?: number;
  code_snippet?: string;
  cwe_id?: string;
  owasp_category?: string;
  detection_source: DetectionSource;
  confidence_score: number;
  mitigation?: string;
  false_positive_flag: boolean;
  created_at: string;
}

/**
 * Security scan request
 */
export interface SecurityScanRequest {
  scan_type: 'source_code' | 'config' | 'api' | 'full';
  target_path?: string;
  content?: string;
  detection_mode: 'full' | 'rules_only' | 'ml_only' | 'critical_only';
  include_mitigations: boolean;
}

/**
 * Security scan result
 */
export interface SecurityScanResult {
  scan_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  scan_type: string;
  detection_mode: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  vulnerabilities: Vulnerability[];
  summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  rule_detections: number;
  ml_detections: number;
  hybrid_detections: number;
}

/**
 * Security rule for rule-based detection
 */
export interface SecurityRule {
  id: string;
  name: string;
  description: string;
  category: VulnerabilityCategory;
  severity: VulnerabilitySeverity;
  pattern: string;
  pattern_type: 'regex' | 'ast' | 'semantic';
  cwe_id?: string;
  owasp_category?: string;
  is_active: boolean;
  false_positive_rate?: number;
  created_at: string;
  updated_at: string;
}

/**
 * Security rule create/update request
 */
export interface SecurityRuleRequest {
  name: string;
  description: string;
  category: VulnerabilityCategory;
  severity: VulnerabilitySeverity;
  pattern: string;
  pattern_type: 'regex' | 'ast' | 'semantic';
  cwe_id?: string;
  owasp_category?: string;
  is_active: boolean;
}

/**
 * Training configuration
 */
export interface TrainingConfig {
  epochs: number;
  batch_size: number;
  learning_rate: number;
  early_stopping_patience: number;
  class_weights_enabled: boolean;
  focal_loss_enabled: boolean;
  validation_split: number;
}

/**
 * Training run record
 */
export interface TrainingRun {
  id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  config: TrainingConfig;
  started_at: string;
  completed_at?: string;
  current_epoch?: number;
  total_epochs: number;
  metrics: TrainingMetrics;
  best_checkpoint?: string;
}

/**
 * Training metrics
 */
export interface TrainingMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  false_negative_rate: number;
  mcc?: number; // Matthews Correlation Coefficient
  loss: number;
  val_accuracy?: number;
  val_loss?: number;
  class_metrics?: Record<string, {
    precision: number;
    recall: number;
    f1_score: number;
    support: number;
  }>;
}

/**
 * Model evaluation result
 */
export interface EvaluationResult {
  id: string;
  model_version: string;
  evaluated_at: string;
  dataset_size: number;
  metrics: TrainingMetrics;
  confusion_matrix: number[][];
  class_labels: string[];
  threshold: number;
  roc_auc?: number;
  pr_auc?: number;
}

/**
 * Continuous learning feedback
 */
export interface FeedbackRecord {
  id: string;
  vulnerability_id: string;
  feedback_type: 'false_positive' | 'false_negative' | 'correct' | 'severity_change';
  original_prediction: string;
  corrected_label?: string;
  notes?: string;
  submitted_by: string;
  submitted_at: string;
  used_in_retraining: boolean;
}

/**
 * Migration status for Huawei Cloud
 */
export interface MigrationStatus {
  phase: 'local' | 'preparing' | 'migrating' | 'cloud';
  components: {
    name: string;
    status: 'not_started' | 'in_progress' | 'completed' | 'blocked';
    progress_percent: number;
    notes?: string;
  }[];
  target_platform: 'huawei_modelarts' | 'huawei_eis';
  estimated_completion?: string;
  blockers: string[];
  last_updated: string;
}

/**
 * Security dashboard stats
 */
export interface SecurityDashboardStats {
  total_scans: number;
  total_vulnerabilities: number;
  open_vulnerabilities: number;
  resolved_vulnerabilities: number;
  severity_distribution: Record<VulnerabilitySeverity, number>;
  category_distribution: Record<VulnerabilityCategory, number>;
  detection_source_distribution: Record<DetectionSource, number>;
  recent_scans: SecurityScanResult[];
  top_vulnerabilities: Vulnerability[];
  model_accuracy: number;
  false_positive_rate: number;
}
