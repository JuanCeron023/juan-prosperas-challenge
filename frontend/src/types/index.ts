export type JobStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface Job {
  job_id: string;
  user_id: string;
  status: JobStatus;
  report_type: string;
  created_at: string;
  updated_at: string;
  result_url: string | null;
}

export interface JobCreatePayload {
  report_type: "sales" | "inventory" | "analytics";
  date_range: { start_date: string; end_date: string };
  format: "csv" | "pdf" | "json";
  priority?: "standard" | "high";
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  next_cursor: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ErrorResponse {
  detail: string;
  field?: string;
}

export const STATUS_COLORS: Record<JobStatus, string> = {
  PENDING: "yellow",
  PROCESSING: "blue",
  COMPLETED: "green",
  FAILED: "red",
};
