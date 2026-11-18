import type {
  HistoryEntry,
  NewTicketPayload,
  Notification,
  Operator,
  Ticket,
  TicketDetail,
  TicketFilters,
  TransitionPayload,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: FieldError[];

  constructor(message: string, status: number, code: string, details: FieldError[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0, "NETWORK_ERROR");
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = body?.error;
    throw new ApiError(
      error?.message ?? "Unexpected server response.",
      response.status,
      error?.code ?? "UNKNOWN_ERROR",
      error?.details ?? [],
    );
  }
  return body as T;
}

function toQuery(filters: TicketFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const api = {
  listTickets: (filters: TicketFilters) => request<Ticket[]>(`/tickets${toQuery(filters)}`),
  getTicket: (ticketId: number) => request<TicketDetail>(`/tickets/${ticketId}`),
  createTicket: (payload: NewTicketPayload) =>
    request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(payload) }),
  changeStatus: (ticketId: number, payload: TransitionPayload) =>
    request<Ticket>(`/tickets/${ticketId}/transitions`, { method: "POST", body: JSON.stringify(payload) }),
  addComment: (ticketId: number, comment: string, actor: string) =>
    request<HistoryEntry>(`/tickets/${ticketId}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment, actor }),
    }),
  assignTicket: (ticketId: number, operatorId: number, actor: string) =>
    request<Ticket>(`/tickets/${ticketId}/assignment`, {
      method: "PUT",
      body: JSON.stringify({ operator_id: operatorId, actor }),
    }),
  listOperators: () => request<Operator[]>("/operators"),
  listNotifications: (limit = 15) => request<Notification[]>(`/notifications?limit=${limit}`),
};
