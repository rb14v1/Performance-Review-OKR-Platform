export type Role = "employee" | "manager" | "hr_admin";

export interface UserBrief {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  title?: string;
}

export interface User extends UserBrief {
  manager: UserBrief | null;
  department: Department | null;
}

export interface Department {
  id: number;
  name: string;
  parent_department: number | null;
}

export type ObjectiveStatus = "draft" | "active" | "completed" | "cancelled";

export interface Objective {
  id: number;
  owner: UserBrief;
  cycle: number;
  parent_objective: number | null;
  title: string;
  description: string;
  status: ObjectiveStatus;
  progress_pct: string;
  created_at: string;
  updated_at: string;
  key_results?: KeyResult[];
  child_objectives?: Objective[];
}

export type MetricType = "number" | "percentage" | "boolean" | "currency";

export interface KeyResult {
  id: number;
  objective: number;
  title: string;
  metric_type: MetricType;
  start_value: string;
  target_value: string;
  current_value: string;
  weight: string | null;
  progress_pct: string;
  check_ins?: CheckIn[];
}

export type ConfidenceLevel = "low" | "medium" | "high";

export interface CheckIn {
  id: number;
  key_result: number;
  value: string;
  confidence_level: ConfidenceLevel;
  comment: string;
  created_by: UserBrief;
  created_at: string;
}

export type CycleStatus =
  | "draft"
  | "self_review"
  | "manager_review"
  | "peer_feedback"
  | "calibration"
  | "closed";

export interface ReviewCycle {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: CycleStatus;
}

export interface SelfReview {
  id: number;
  cycle: number;
  employee: UserBrief;
  accomplishments: string;
  challenges: string;
  self_rating: string;
  submitted_at: string | null;
}

export interface ManagerReview {
  id: number;
  cycle: number;
  employee: UserBrief;
  manager: UserBrief;
  manager_at_cycle_start: number | null;
  draft_rating: string;
  comments: string;
  submitted_at: string | null;
}

export interface Rating {
  id: number;
  cycle: number;
  employee: UserBrief;
  final_rating: string;
  rating_source: "manager" | "calibration";
  finalized_by: number | null;
  finalized_at: string | null;
  acknowledged_by_employee: boolean;
  acknowledged_at: string | null;
}

export type FeedbackRequestStatus = "pending" | "accepted" | "declined";
export type Relationship = "peer" | "manager" | "direct_report" | "self";

export interface FeedbackRequest {
  id: number;
  cycle: number;
  subject: UserBrief;
  reviewer: UserBrief;
  relationship: Relationship;
  status: FeedbackRequestStatus;
  created_at: string;
}

export type AnonymityMode = "anonymous" | "named";

export interface PeerFeedback {
  id: number;
  cycle: number;
  subject: UserBrief;
  reviewer: UserBrief | null;
  relationship: Relationship;
  anonymity_mode: AnonymityMode;
  strengths: string;
  improvements: string;
  submitted_at: string;
}

export interface CalibrationSession {
  id: number;
  cycle: number;
  department: Department;
  status: "open" | "closed";
  entries: CalibrationEntry[];
}

export interface CalibrationEntry {
  id: number;
  session: number;
  employee: UserBrief;
  pre_rating: string;
  post_rating: string;
  adjustment_reason: string;
  resolved: boolean;
}

export interface TeamProgressRow {
  user_id: number;
  email: string;
  name: string;
  objective_count: number;
  average_progress_pct: number;
}

export interface OrgProgressRow {
  department_id: number;
  department_name: string;
  objective_count: number;
  average_progress_pct: number;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
