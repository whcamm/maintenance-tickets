import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import {
  STATUS_LABELS,
  STATUS_ORDER,
  type Notification,
  type Operator,
  type Ticket,
  type TicketFilters,
  type TicketStatus,
} from "./api/types";
import { AppHeader } from "./components/AppHeader";
import { NewTicketForm } from "./components/NewTicketForm";
import { TicketBoard } from "./components/TicketBoard";
import { TicketDrawer } from "./components/TicketDrawer";
import { TicketFiltersBar } from "./components/TicketFiltersBar";

interface Toast {
  kind: "success" | "error";
  message: string;
}

interface Selection {
  ticketId: number;
  target: TicketStatus | null;
}

export default function App() {
  const [operators, setOperators] = useState<Operator[]>([]);
  const [actingOperatorId, setActingOperatorId] = useState<number | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [filters, setFilters] = useState<TicketFilters>({});
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [lastSeenNotificationId, setLastSeenNotificationId] = useState(0);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

  const actor = operators.find((operator) => operator.id === actingOperatorId)?.full_name ?? "Operator";

  const showToast = useCallback((kind: Toast["kind"], message: string) => setToast({ kind, message }), []);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      setTickets(await api.listTickets(filters));
    } catch (error) {
      showToast("error", error instanceof Error ? error.message : "Tickets could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [filters, showToast]);

  const loadNotifications = useCallback(async () => {
    try {
      setNotifications(await api.listNotifications());
    } catch {
      setNotifications([]);
    }
  }, []);

  useEffect(() => {
    api
      .listOperators()
      .then((items) => {
        setOperators(items);
        setActingOperatorId((current) => current ?? items[0]?.id ?? null);
      })
      .catch((error) => showToast("error", error.message));
    api
      .listNotifications()
      .then((items) => {
        setNotifications(items);
        setLastSeenNotificationId(items[0]?.id ?? 0);
      })
      .catch(() => setNotifications([]));
  }, [showToast]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 4500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const refresh = useCallback(async () => {
    await Promise.all([loadTickets(), loadNotifications()]);
  }, [loadTickets, loadNotifications]);

  const handleCreated = (ticket: Ticket) => {
    showToast("success", `Ticket #${ticket.id} created.`);
    refresh();
  };

  const handleChanged = (_: Ticket, message: string) => {
    showToast("success", message);
    refresh();
  };

  const handleMove = async (ticket: Ticket, target: TicketStatus) => {
    const rule = ticket.allowed_transitions.find((transition) => transition.to_status === target);
    if (rule && ((rule.requires_diagnosis && !ticket.diagnosis) || rule.requires_comment)) {
      setSelection({ ticketId: ticket.id, target });
      return;
    }
    try {
      await api.changeStatus(ticket.id, { to_status: target, actor });
      showToast("success", `Ticket #${ticket.id} moved to ${STATUS_LABELS[target]}.`);
    } catch (error) {
      showToast("error", error instanceof Error ? error.message : "The transition was rejected.");
    }
    refresh();
  };

  const unreadCount = notifications.filter((notification) => notification.id > lastSeenNotificationId).length;

  return (
    <div className="app">
      <AppHeader
        operators={operators}
        actingOperatorId={actingOperatorId}
        onActingOperatorChange={setActingOperatorId}
        notifications={notifications}
        unreadCount={unreadCount}
        onOpenNotifications={() => setLastSeenNotificationId(notifications[0]?.id ?? lastSeenNotificationId)}
      />

      <main className="layout">
        <NewTicketForm operators={operators} onCreated={handleCreated} />
        <div className="board-area">
          <TicketFiltersBar filters={filters} operators={operators} onChange={setFilters} />
          <p className="hint muted small">
            Drag a card to another column or open it to change its status. Invalid transitions are rejected by the
            server.
          </p>
          <TicketBoard
            tickets={tickets}
            visibleStatuses={filters.status ? [filters.status] : STATUS_ORDER}
            loading={loading}
            onSelect={(ticket) => setSelection({ ticketId: ticket.id, target: null })}
            onMove={handleMove}
          />
        </div>
      </main>

      {selection && (
        <TicketDrawer
          key={selection.ticketId}
          ticketId={selection.ticketId}
          initialTarget={selection.target}
          operators={operators}
          actor={actor}
          onClose={() => setSelection(null)}
          onChanged={handleChanged}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.kind}`} role="status">
          {toast.message}
        </div>
      )}
    </div>
  );
}
