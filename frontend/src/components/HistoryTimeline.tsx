import { STATUS_LABELS, type HistoryEntry } from "../api/types";
import { formatDateTime } from "../utils/format";

function describe(entry: HistoryEntry): string {
  switch (entry.event_type) {
    case "CREATED":
      return "Ticket created";
    case "STATUS_CHANGED":
      return `${entry.from_status ? STATUS_LABELS[entry.from_status] : "-"} → ${
        entry.to_status ? STATUS_LABELS[entry.to_status] : "-"
      }`;
    case "ASSIGNED":
      return "Assignment";
    case "COMMENT":
      return "Comment";
  }
}

export function HistoryTimeline({ entries }: { entries: HistoryEntry[] }) {
  return (
    <ol className="timeline">
      {entries.map((entry) => (
        <li key={entry.id} className={`timeline-item event-${entry.event_type}`}>
          <div className="timeline-head">
            <strong>{describe(entry)}</strong>
            <span className="muted small">{formatDateTime(entry.created_at)}</span>
          </div>
          {entry.comment && <p>{entry.comment}</p>}
          <span className="muted small">by {entry.actor}</span>
        </li>
      ))}
    </ol>
  );
}
