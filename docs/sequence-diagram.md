# Sequence Analysis

Main flow: a reporter creates a ticket and an operator moves it through the workflow. Every status change is persisted together with a history entry by a stored procedure.

## 1. Create ticket

```mermaid
sequenceDiagram
    autonumber
    actor Reporter
    participant UI as React frontend
    participant API as FastAPI router
    participant Service as TicketService
    participant Repo as TicketRepository
    participant DB as MySQL

    Reporter->>UI: Fill title, asset code, description, reporter
    UI->>API: POST /api/tickets
    API->>API: Validate payload (Pydantic)
    alt Invalid payload
        API-->>UI: 422 VALIDATION_ERROR with field details
        UI-->>Reporter: Show field errors
    else Valid payload
        API->>Service: create_ticket(new_ticket)
        Service->>Repo: create(new_ticket)
        Repo->>DB: CALL sp_create_ticket(...)
        activate DB
        DB->>DB: START TRANSACTION
        DB->>DB: INSERT tickets (status = PENDING)
        DB->>DB: INSERT ticket_history (CREATED)
        DB->>DB: COMMIT
        DB-->>Repo: ticket_id
        deactivate DB
        Service->>Repo: get(ticket_id)
        Repo->>DB: SELECT ticket
        DB-->>Repo: row
        Repo-->>Service: Ticket
        Service-->>API: Ticket
        API-->>UI: 201 Created + ticket and allowed transitions
        UI-->>Reporter: Card appears in the Pending column
    end
```

## 2. Status transition with history

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant UI as React frontend
    participant API as FastAPI router
    participant Service as TicketService
    participant Workflow as TicketWorkflow
    participant Repo as TicketRepository
    participant DB as MySQL
    participant Notifier as NotificationService

    Operator->>UI: Move ticket to Resolved and enter diagnosis
    UI->>API: POST /api/tickets/{id}/transitions
    API->>Service: change_status(id, RESOLVED, actor, diagnosis)
    Service->>Repo: get(id)
    Repo->>DB: SELECT ticket
    DB-->>Repo: current status
    Service->>Workflow: validate(current, RESOLVED, diagnosis)
    alt Transition not in the state machine
        Workflow-->>Service: InvalidTransitionError
        Service-->>API: error
        API-->>UI: 409 INVALID_TRANSITION
    else Missing diagnosis or comment
        Workflow-->>Service: BusinessRuleViolationError
        Service-->>API: error
        API-->>UI: 422 BUSINESS_RULE_VIOLATION
    else Valid transition
        Workflow-->>Service: rule
        Service->>Repo: transition(id, RESOLVED, diagnosis, comment, actor)
        Repo->>DB: CALL sp_transition_ticket_status(...)
        activate DB
        DB->>DB: START TRANSACTION
        DB->>DB: SELECT ... FOR UPDATE (lock ticket)
        DB->>DB: Check ticket_status_transitions and required fields
        alt Rule violated at database level
            DB->>DB: ROLLBACK
            DB-->>Repo: SIGNAL 5409 / 5422
            Repo-->>API: domain error (409 / 422)
        else Rule satisfied
            DB->>DB: UPDATE tickets SET status, diagnosis
            DB->>DB: INSERT ticket_history (STATUS_CHANGED)
            DB->>DB: COMMIT
            DB-->>Repo: history_id
            Service->>Notifier: notify_status_change(ticket, previous, history_id)
            Notifier->>DB: INSERT notifications (simulated email)
            Service-->>API: updated Ticket
            API-->>UI: 200 OK + ticket and next allowed transitions
            UI-->>Operator: Card moves to Resolved, history updated
        end
        deactivate DB
    end
```

## State machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: ticket created
    PENDING --> IN_PROGRESS: start work
    PENDING --> RESOLVED: quick fix (diagnosis required)
    IN_PROGRESS --> PENDING: on hold (comment required)
    IN_PROGRESS --> RESOLVED: fixed (diagnosis required)
    RESOLVED --> IN_PROGRESS: reopen (comment required)
    RESOLVED --> CLOSED: confirmed
    CLOSED --> [*]
```

Any pair not shown above (for example `PENDING → CLOSED` or `CLOSED → IN_PROGRESS`) is rejected with `409`.
