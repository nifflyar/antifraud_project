// ============ Auth ============
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  is_admin?: boolean;
}

export interface SuccessResponse {
  success: boolean;
}

// ============ User ============
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  created_at: string;
}

export interface UserListItem {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface ListUsersResponse {
  users: UserListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface UpdateUserRequest {
  full_name?: string;
  is_admin?: boolean;
}

// ============ Dashboard ============
export interface DashboardSummary {
  total_passengers: number;
  high_risk_count: number;
  critical_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  high_risk_pct: number;
  critical_risk_pct: number;
  medium_risk_pct: number;
  low_risk_pct: number;
  share_suspicious_ops: number;
  top_risk_channel: string | null;
  top_risk_terminal: string | null;
}

export interface RiskTrendItem {
  date: string;
  total_ops: number;
  highrisk_ops: number;
  critical_ops?: number;
  share: number;
}

export interface RiskTrendResponse {
  items: RiskTrendItem[];
}

export interface RiskConcentrationItem {
  dimension_value: string;
  total_ops: number;
  highrisk_ops: number;
  share_highrisk_ops: number;
  lift_vs_base: number;
}

export interface RiskConcentrationResponse {
  dimension_type: string;
  items: RiskConcentrationItem[];
}

export interface RiskStatsResponse {
  period: string;
  date_from: string | null;
  date_to: string | null;
  total_passengers: number;
  total_ops: number;
  critical_ops: number;
  high_ops: number;
  medium_ops: number;
  low_ops: number;
  critical_pct: number;
  high_pct: number;
  medium_pct: number;
  low_pct: number;
}

// ============ Passengers ============
export type RiskBand = "low" | "medium" | "high" | "critical";

export interface PassengerListItem {
  id: string;
  fio_clean: string;
  fake_fio_score: number;
  last_seen_at: string;
  risk_band: RiskBand;
  final_score: number;
}

export interface PassengerListResponse {
  items: PassengerListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface PassengerTransactionsResponse {
  items: PassengerTransaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface PassengerFeatures {
  total_tickets: number;
  refund_cnt: number;
  refund_share: number;
  night_tickets: number;
  night_share: number;
  max_tickets_month?: number;
  max_tickets_same_depday?: number;
  late_refunds?: number;
  late_refund_share?: number;
  very_late_refunds?: number;
  very_late_refund_share?: number;
  quick_refunds?: number;
  quick_refund_share?: number;
  refund_close_ratio?: number;
  tickets_per_train_peak?: number;
  fio_fake_score_max: number;
  activity_days?: number;
  suspicious_refund_pattern_cnt?: number;
  refund_amount_diversity?: number;
  seat_blocking_flag?: boolean;
}

export interface PassengerScore {
  rule_score: number;
  ml_score: number;
  final_score: number;
  risk_band: RiskBand;
  top_reasons: string[];
  seat_blocking_flag: boolean;
  is_manual: boolean;
  scored_at: string | null;
}

export interface PassengerIdentity {
  iin: string | null;
  doc_no: string | null;
  phone: string | null;
  gender: string | null;
  raw_fio: string | null;
  channels: string[];
  aggregators: string[];
  terminals: string[];
  branches: string[];
  sale_users: string[];
  carriers: string[];
  tariff_types: string[];
  service_classes: string[];
  routes: string[];
  train_numbers: string[];
  distinct_iin_count: number;
  distinct_doc_count: number;
  distinct_phone_count: number;
  distinct_terminal_count: number;
  distinct_route_count: number;
  first_operation_at: string | null;
  last_operation_at: string | null;
}

export interface PassengerProfile {
  id: string;
  fio_clean: string;
  fake_fio_score: number;
  first_seen_at: string;
  last_seen_at: string;
  identity: PassengerIdentity | null;
  features: PassengerFeatures | null;
  score: PassengerScore | null;
}

export interface PassengerTransaction {
  id: string;
  op_type: string;
  op_datetime: string;
  dep_datetime: string | null;
  train_no: string | null;
  amount: number;
  fee: number;
  channel: string | null;
  aggregator: string | null;
  terminal: string | null;
  cashdesk: string | null;
  point_of_sale: string | null;
  order_no: string | null;
  ticket_no: string | null;
  tariff_type: string | null;
  service_class: string | null;
  dep_station: string | null;
  arr_station: string | null;
  route: string | null;
  fio: string | null;
  iin: string | null;
  doc_no: string | null;
  phone: string | null;
  gender: string | null;
  branch: string | null;
  sale_user: string | null;
  carrier: string | null;
  settlement_type: string | null;
}

export interface RiskOverrideRequest {
  new_risk_band: RiskBand;
  reason: string;
}

// ============ Operations ============
export interface SuspiciousOperation {
  id: string;
  passenger_id: string;
  op_type: string;
  op_datetime: string;
  dep_datetime: string | null;
  train_no: string | null;
  amount: number;
  fee: number;
  channel: string | null;
  aggregator: string | null;
  terminal: string | null;
  cashdesk: string | null;
  point_of_sale: string | null;
  order_no: string | null;
  ticket_no: string | null;
  tariff_type: string | null;
  service_class: string | null;
  dep_station: string | null;
  arr_station: string | null;
  route: string | null;
  fio: string | null;
  iin: string | null;
  doc_no: string | null;
  phone: string | null;
  gender: string | null;
  branch: string | null;
  sale_user: string | null;
  carrier: string | null;
  settlement_type: string | null;
  risk_band: RiskBand;
  operation_risk_score: number;
  operation_reasons: string[];
}

export interface SuspiciousOperationsResponse {
  items: SuspiciousOperation[];
  total: number;
  limit: number;
  offset: number;
  risk_stats?: {
    low: number;
    medium: number;
    high: number;
    critical: number;
    suspicious: number;
    high_critical: number;
  } | null;
}

// ============ Uploads ============
export interface UploadResponse {
  id: string;
  filename: string;
  status: string;
  uploaded_at: string;
  uploaded_by_user_id: string | null;
}

export interface UploadListResponse {
  items: UploadResponse[];
  total: number;
  limit: number;
  offset: number;
}

// ============ Scoring ============
export type ScoringStatus = "pending" | "running" | "done" | "failed";

export interface ScoringRunRequest {
  upload_id: number;
}

export interface ScoringRunResponse {
  job_id: string;
  status: ScoringStatus;
  started_at: string;
}

export interface ScoringStatusResponse {
  job_id: string;
  upload_id: number;
  status: ScoringStatus;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
}

// ============ Audit ============
export interface AuditLogItem {
  id: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  user_id: string | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogsResponse {
  items: AuditLogItem[];
  logs?: AuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}
