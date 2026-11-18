import { useState } from "react";
import type { Notification, Operator } from "../api/types";
import { formatRelative, initials } from "../utils/format";

interface AppHeaderProps {
  operators: Operator[];
  actingOperatorId: number | null;
  onActingOperatorChange: (operatorId: number) => void;
  notifications: Notification[];
  unreadCount: number;
  onOpenNotifications: () => void;
}

export function AppHeader({
  operators,
  actingOperatorId,
  onActingOperatorChange,
  notifications,
  unreadCount,
  onOpenNotifications,
}: AppHeaderProps) {
  const [open, setOpen] = useState(false);
  const actingOperator = operators.find((operator) => operator.id === actingOperatorId);

  const toggle = () => {
    if (!open) onOpenNotifications();
    setOpen(!open);
  };

  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          ▲
        </span>
        <span className="brand-title">Maintenance · Tickets</span>
      </div>
      <div className="header-actions">
        <div className="notifications">
          <button type="button" className="icon-button bell" onClick={toggle} aria-label="Notifications">
            🔔
            {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
          </button>
          {open && (
            <div className="notifications-panel">
              <h3>Notifications (simulated email)</h3>
              {notifications.length === 0 && <p className="muted">No notifications yet.</p>}
              <ul>
                {notifications.map((notification) => (
                  <li key={notification.id}>
                    <p>{notification.message}</p>
                    <span className="muted small">
                      To {notification.recipient} · {formatRelative(notification.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <label className="acting-as">
          <span className="muted small">Operator</span>
          <select
            value={actingOperatorId ?? ""}
            onChange={(event) => onActingOperatorChange(Number(event.target.value))}
            aria-label="Acting operator"
          >
            {operators.map((operator) => (
              <option key={operator.id} value={operator.id}>
                {operator.full_name}
              </option>
            ))}
          </select>
        </label>
        <span className="avatar large">{actingOperator ? initials(actingOperator.full_name) : "OP"}</span>
      </div>
    </header>
  );
}
