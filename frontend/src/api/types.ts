export type TicketStatus = "PENDING" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export type HistoryEventType = "CREATED" | "STATUS_CHANGED" | "COMMENT" | "ASSIGNED";

export const STATUS_ORDER: TicketStatus[] = ["PENDING", "IN_PROGRESS", "RESOLVED", "CLOSED"];

export const STATUS_LABELS: Record<TicketStatus, string> = {
  PENDING: "Pending",
  IN_PROGRESS: "In Progress",
  RESOLVED: "Resolved",
  CLOSED: "Closed",
};

export interface Transition {
  from_status: TicketStatus;
  to_status: TicketStatus;
  requires_diagnosis: boolean;
  requires_comment: boolean;
}

export interface Ticket {
  id: number;
  title: string;
  asset_code: string;
  description: string | null;
  status: TicketStatus;
  diagnosis: string | null;
  reported_by: string;
  assigned_operator_id: number | null;
  assigned_operator_name: string | null;
  created_at: string;
  updated_at: string;
  allowed_transitions: Transition[];
}

export interface HistoryEntry {
  id: number;
  ticket_id: number;
  event_type: HistoryEventType;
  from_status: TicketStatus | null;
  to_status: TicketStatus | null;
  comment: string | null;
  actor: string;
  created_at: string;
}

export interface TicketDetail extends Ticket {
  history: HistoryEntry[];
}

export interface Operator {
  id: number;
  full_name: string;
  email: string;
}

export interface Notification {
  id: number;
  ticket_id: number;
  recipient: string;
  channel: string;
  message: string;
  created_at: string;
}

export interface TicketFilters {
  status?: TicketStatus;
  operator_id?: number;
  created_from?: string;
  created_to?: string;
}

export interface NewTicketPayload {
  title: string;
  asset_code: string;
  description: string | null;
  reported_by: string;
  assigned_operator_id: number | null;
}

export interface TransitionPayload {
  to_status: TicketStatus;
  actor: string;
  diagnosis?: string;
  comment?: string;
}
