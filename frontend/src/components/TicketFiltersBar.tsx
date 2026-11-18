import { STATUS_LABELS, STATUS_ORDER, type Operator, type TicketFilters, type TicketStatus } from "../api/types";

interface TicketFiltersBarProps {
  filters: TicketFilters;
  operators: Operator[];
  onChange: (filters: TicketFilters) => void;
}

export function TicketFiltersBar({ filters, operators, onChange }: TicketFiltersBarProps) {
  const set = (changes: Partial<TicketFilters>) => onChange({ ...filters, ...changes });
  const hasFilters = Object.values(filters).some((value) => value !== undefined && value !== "");

  return (
    <div className="filters">
      <label>
        Status
        <select
          value={filters.status ?? ""}
          onChange={(event) => set({ status: (event.target.value || undefined) as TicketStatus | undefined })}
        >
          <option value="">All</option>
          {STATUS_ORDER.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Operator
        <select
          value={filters.operator_id ?? ""}
          onChange={(event) => set({ operator_id: event.target.value ? Number(event.target.value) : undefined })}
        >
          <option value="">All</option>
          {operators.map((operator) => (
            <option key={operator.id} value={operator.id}>
              {operator.full_name}
            </option>
          ))}
        </select>
      </label>
      <label>
        From
        <input
          type="date"
          value={filters.created_from ?? ""}
          max={filters.created_to}
          onChange={(event) => set({ created_from: event.target.value || undefined })}
        />
      </label>
      <label>
        To
        <input
          type="date"
          value={filters.created_to ?? ""}
          min={filters.created_from}
          onChange={(event) => set({ created_to: event.target.value || undefined })}
        />
      </label>
      {hasFilters && (
        <button type="button" className="button ghost" onClick={() => onChange({})}>
          Clear filters
        </button>
      )}
    </div>
  );
}
