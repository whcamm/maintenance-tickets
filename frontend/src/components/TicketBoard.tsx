import { useState, type DragEvent } from "react";
import { STATUS_LABELS, STATUS_ORDER, type Ticket, type TicketStatus } from "../api/types";
import { formatRelative, initials } from "../utils/format";

interface TicketBoardProps {
  tickets: Ticket[];
  visibleStatuses?: TicketStatus[];
  loading: boolean;
  onSelect: (ticket: Ticket) => void;
  onMove: (ticket: Ticket, target: TicketStatus) => void;
}

export function TicketBoard({ tickets, visibleStatuses = STATUS_ORDER, loading, onSelect, onMove }: TicketBoardProps) {
  const [dragOver, setDragOver] = useState<TicketStatus | null>(null);

  const handleDrop = (event: DragEvent, target: TicketStatus) => {
    event.preventDefault();
    setDragOver(null);
    const ticketId = Number(event.dataTransfer.getData("text/plain"));
    const ticket = tickets.find((item) => item.id === ticketId);
    if (ticket && ticket.status !== target) onMove(ticket, target);
  };

  return (
    <div className="board" style={{ gridTemplateColumns: `repeat(${visibleStatuses.length}, minmax(220px, 1fr))` }}>
      {visibleStatuses.map((status) => {
        const columnTickets = tickets.filter((ticket) => ticket.status === status);
        return (
          <section
            key={status}
            className={`column ${dragOver === status ? "drag-over" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(status);
            }}
            onDragLeave={() => setDragOver(null)}
            onDrop={(event) => handleDrop(event, status)}
            aria-label={`${STATUS_LABELS[status]} tickets`}
          >
            <header className="column-header">
              <span className={`status-pill status-${status}`}>{STATUS_LABELS[status]}</span>
              <span className="count">{columnTickets.length}</span>
            </header>
            {loading && columnTickets.length === 0 && <p className="empty">Loading...</p>}
            {!loading && columnTickets.length === 0 && <p className="empty">No tickets</p>}
            {columnTickets.map((ticket) => (
              <article
                key={ticket.id}
                className="card"
                draggable
                tabIndex={0}
                onDragStart={(event) => event.dataTransfer.setData("text/plain", String(ticket.id))}
                onClick={() => onSelect(ticket)}
                onKeyDown={(event) => event.key === "Enter" && onSelect(ticket)}
              >
                <div className="card-top">
                  <span className="ticket-id">#{ticket.id}</span>
                  <span className="muted small">{formatRelative(ticket.created_at)}</span>
                </div>
                <h3>{ticket.title}</h3>
                <div className="card-bottom">
                  <span className={`asset asset-${status}`}>{ticket.asset_code}</span>
                  {ticket.assigned_operator_name ? (
                    <span className="avatar" title={ticket.assigned_operator_name}>
                      {initials(ticket.assigned_operator_name)}
                    </span>
                  ) : (
                    <span className="muted small">Unassigned</span>
                  )}
                </div>
              </article>
            ))}
          </section>
        );
      })}
    </div>
  );
}
