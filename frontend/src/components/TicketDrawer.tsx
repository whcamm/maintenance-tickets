import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import { STATUS_LABELS, type Operator, type Ticket, type TicketDetail, type TicketStatus } from "../api/types";
import { formatDateTime } from "../utils/format";
import { HistoryTimeline } from "./HistoryTimeline";

interface TicketDrawerProps {
  ticketId: number;
  operators: Operator[];
  actor: string;
  initialTarget: TicketStatus | null;
  onClose: () => void;
  onChanged: (ticket: Ticket, message: string) => void;
}

const errorMessage = (error: unknown) => (error instanceof Error ? error.message : "Unexpected error.");

export function TicketDrawer({ ticketId, operators, actor, initialTarget, onClose, onChanged }: TicketDrawerProps) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [target, setTarget] = useState<TicketStatus | null>(initialTarget);
  const [diagnosis, setDiagnosis] = useState("");
  const [transitionComment, setTransitionComment] = useState("");
  const [newComment, setNewComment] = useState("");
  const [operatorId, setOperatorId] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const detail = await api.getTicket(ticketId);
      setTicket(detail);
      setOperatorId(detail.assigned_operator_id ? String(detail.assigned_operator_id) : "");
      setLoadError(null);
    } catch (error) {
      setLoadError(errorMessage(error));
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setTarget(initialTarget);
  }, [initialTarget]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const run = async (action: () => Promise<Ticket | unknown>, message: string) => {
    setBusy(true);
    setActionError(null);
    try {
      const result = await action();
      await load();
      if (result && typeof result === "object" && "status" in result) onChanged(result as Ticket, message);
      else if (ticket) onChanged(ticket, message);
      return true;
    } catch (error) {
      setActionError(errorMessage(error));
      return false;
    } finally {
      setBusy(false);
    }
  };

  const rule = ticket?.allowed_transitions.find((transition) => transition.to_status === target);

  const submitTransition = async (event: FormEvent) => {
    event.preventDefault();
    if (!target || !ticket) return;
    const done = await run(
      () =>
        api.changeStatus(ticket.id, {
          to_status: target,
          actor,
          diagnosis: diagnosis.trim() || undefined,
          comment: transitionComment.trim() || undefined,
        }),
      `Ticket #${ticket.id} moved to ${STATUS_LABELS[target]}.`,
    );
    if (done) {
      setTarget(null);
      setDiagnosis("");
      setTransitionComment("");
    }
  };

  const submitComment = async (event: FormEvent) => {
    event.preventDefault();
    if (!ticket) return;
    const done = await run(() => api.addComment(ticket.id, newComment, actor), `Comment added to #${ticket.id}.`);
    if (done) setNewComment("");
  };

  const submitAssignment = async () => {
    if (!ticket || !operatorId) return;
    await run(
      () => api.assignTicket(ticket.id, Number(operatorId), actor),
      `Ticket #${ticket.id} assigned.`,
    );
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()} aria-label="Ticket detail">
        <header className="drawer-header">
          <div>
            <span className="ticket-id">#{ticketId}</span>
            <h2>{ticket?.title ?? "Loading..."}</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        {loadError && <p className="form-error">{loadError}</p>}

        {ticket && (
          <div className="drawer-body">
            <dl className="details">
              <div>
                <dt>Status</dt>
                <dd>
                  <span className={`status-pill status-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>
                </dd>
              </div>
              <div>
                <dt>Asset</dt>
                <dd>{ticket.asset_code}</dd>
              </div>
              <div>
                <dt>Reported by</dt>
                <dd>{ticket.reported_by}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{formatDateTime(ticket.created_at)}</dd>
              </div>
            </dl>
            {ticket.description && <p className="description">{ticket.description}</p>}
            {ticket.diagnosis && (
              <p className="diagnosis">
                <strong>Diagnosis:</strong> {ticket.diagnosis}
              </p>
            )}

            {actionError && <p className="form-error" role="alert">{actionError}</p>}

            <section className="drawer-section">
              <h3>Workflow</h3>
              {ticket.allowed_transitions.length === 0 ? (
                <p className="muted">This ticket is closed. No further transitions are allowed.</p>
              ) : (
                <div className="transition-buttons">
                  {ticket.allowed_transitions.map((transition) => (
                    <button
                      key={transition.to_status}
                      type="button"
                      className={`button ${target === transition.to_status ? "primary" : "outline"}`}
                      onClick={() => setTarget(transition.to_status)}
                    >
                      Move to {STATUS_LABELS[transition.to_status]}
                    </button>
                  ))}
                </div>
              )}

              {target && (
                <form className="transition-form" onSubmit={submitTransition}>
                  {!rule && (
                    <p className="form-hint">
                      {STATUS_LABELS[ticket.status]} → {STATUS_LABELS[target]} is not part of the workflow. The server
                      will reject it.
                    </p>
                  )}
                  {(rule?.requires_diagnosis || target === "RESOLVED") && (
                    <>
                      <label htmlFor="diagnosis">
                        Diagnosis {rule?.requires_diagnosis && !ticket.diagnosis ? "(required)" : "(optional)"}
                      </label>
                      <textarea
                        id="diagnosis"
                        rows={3}
                        value={diagnosis}
                        onChange={(event) => setDiagnosis(event.target.value)}
                        placeholder={ticket.diagnosis ?? "Root cause and fix applied"}
                      />
                    </>
                  )}
                  <label htmlFor="transition-comment">Comment {rule?.requires_comment ? "(required)" : "(optional)"}</label>
                  <textarea
                    id="transition-comment"
                    rows={2}
                    value={transitionComment}
                    onChange={(event) => setTransitionComment(event.target.value)}
                  />
                  <div className="form-actions">
                    <button type="button" className="button ghost" onClick={() => setTarget(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="button primary" disabled={busy}>
                      Confirm {STATUS_LABELS[target]}
                    </button>
                  </div>
                </form>
              )}
            </section>

            {ticket.status !== "CLOSED" && (
              <section className="drawer-section">
                <h3>Assignment</h3>
                <div className="inline-form">
                  <select value={operatorId} onChange={(event) => setOperatorId(event.target.value)}>
                    <option value="">Select operator</option>
                    {operators.map((operator) => (
                      <option key={operator.id} value={operator.id}>
                        {operator.full_name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="button outline"
                    onClick={submitAssignment}
                    disabled={busy || !operatorId || Number(operatorId) === ticket.assigned_operator_id}
                  >
                    Assign
                  </button>
                </div>
              </section>
            )}

            <section className="drawer-section">
              <h3>History</h3>
              <HistoryTimeline entries={ticket.history} />
              {ticket.status !== "CLOSED" && (
                <form className="inline-form" onSubmit={submitComment}>
                  <input
                    value={newComment}
                    onChange={(event) => setNewComment(event.target.value)}
                    placeholder="Add a comment"
                    maxLength={2000}
                  />
                  <button type="submit" className="button outline" disabled={busy || !newComment.trim()}>
                    Comment
                  </button>
                </form>
              )}
            </section>
          </div>
        )}
      </aside>
    </div>
  );
}
