import { useState, type FormEvent } from "react";
import { ApiError, api } from "../api/client";
import type { Operator, Ticket } from "../api/types";

interface NewTicketFormProps {
  operators: Operator[];
  onCreated: (ticket: Ticket) => void;
}

const EMPTY_FORM = { title: "", asset_code: "", description: "", reported_by: "", assigned_operator_id: "" };

export function NewTicketForm({ operators, onCreated }: NewTicketFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (field: keyof typeof EMPTY_FORM, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => ({ ...current, [field]: "" }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const ticket = await api.createTicket({
        title: form.title,
        asset_code: form.asset_code,
        description: form.description || null,
        reported_by: form.reported_by,
        assigned_operator_id: form.assigned_operator_id ? Number(form.assigned_operator_id) : null,
      });
      setForm(EMPTY_FORM);
      setFieldErrors({});
      onCreated(ticket);
    } catch (error) {
      if (error instanceof ApiError && error.details.length > 0) {
        setFieldErrors(Object.fromEntries(error.details.map((detail) => [detail.field, detail.message])));
      }
      setFormError(error instanceof Error ? error.message : "The ticket could not be created.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="panel new-ticket" onSubmit={handleSubmit} noValidate>
      <h2>New ticket</h2>

      <label htmlFor="title">Title</label>
      <input
        id="title"
        value={form.title}
        onChange={(event) => update("title", event.target.value)}
        placeholder="ATM out of service"
        maxLength={120}
        required
      />
      {fieldErrors.title && <p className="field-error">{fieldErrors.title}</p>}

      <label htmlFor="asset_code">Equipment / asset</label>
      <input
        id="asset_code"
        value={form.asset_code}
        onChange={(event) => update("asset_code", event.target.value.toUpperCase())}
        placeholder="ATM-0451"
        maxLength={30}
        required
      />
      {fieldErrors.asset_code && <p className="field-error">{fieldErrors.asset_code}</p>}

      <label htmlFor="description">Description</label>
      <textarea
        id="description"
        value={form.description}
        onChange={(event) => update("description", event.target.value)}
        placeholder="Screen does not respond..."
        rows={3}
        maxLength={2000}
      />

      <label htmlFor="reported_by">Reported by</label>
      <input
        id="reported_by"
        value={form.reported_by}
        onChange={(event) => update("reported_by", event.target.value)}
        placeholder="Your name"
        maxLength={100}
        required
      />
      {fieldErrors.reported_by && <p className="field-error">{fieldErrors.reported_by}</p>}

      <label htmlFor="assigned_operator_id">Assign to (optional)</label>
      <select
        id="assigned_operator_id"
        value={form.assigned_operator_id}
        onChange={(event) => update("assigned_operator_id", event.target.value)}
      >
        <option value="">Unassigned</option>
        {operators.map((operator) => (
          <option key={operator.id} value={operator.id}>
            {operator.full_name}
          </option>
        ))}
      </select>

      {formError && <p className="form-error">{formError}</p>}

      <button type="submit" className="button primary" disabled={submitting}>
        {submitting ? "Creating..." : "Create ticket"}
      </button>
    </form>
  );
}
