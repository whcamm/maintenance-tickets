# Maintenance Tickets

Maintenance ticket control for physical assets such as ATMs and office infrastructure. A reporter creates a ticket and an operator moves it through a validated workflow. Every change is stored in an auditable history.

**Live demo:** https://app-production-cc2fcb7f.up.railway.app  
**API docs (Swagger):** https://app-production-cc2fcb7f.up.railway.app/docs

![Board](docs/mockup/01-board.png)

## Features

- Ticket creation form and a Kanban board with **Pending → In Progress → Resolved → Closed**.
- State machine enforced in the backend **and** in the database (stored procedure + transitions table).
- Business rules: resolving requires a diagnosis; putting a ticket on hold or reopening it requires a comment; closed tickets are final.
- Persisted history of every event (creation, status change, comment, assignment) with actor and timestamp.
- Bonus: operator assignment, filters by status / operator / date range, and simulated e-mail notifications on every status change.
- Controlled error responses (`404`, `409`, `422`, `503`) with a single JSON format; no generic `500` for invalid input.

## Tech stack and rationale

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite | Component model fits the board/drawer UI; TypeScript keeps the API contract typed; Vite gives fast builds and a small bundle. |
| Backend | Python 3.13 + FastAPI | Typed request validation with Pydantic, automatic OpenAPI docs, and a small, readable codebase that is easy to layer. |
| Database | MySQL 8 | Native stored procedures, foreign keys, `CHECK` constraints and row locking (`SELECT ... FOR UPDATE`) cover the integrity requirements. Available as a managed plugin on Railway. |
| DB access | PyMySQL (no ORM) | Writes go through stored procedures by design, so a thin repository over the driver is simpler and more explicit than an ORM. |
| Deployment | Docker on Railway | One image builds the frontend and runs the API, which serves the SPA. One public URL, one service plus the MySQL plugin. |

## Architecture

```
frontend (React) ──HTTP/JSON──> api (routers) ──> services ──> domain (TicketWorkflow)
                                                      │
                                                      └──> repositories ──CALL sp_*──> MySQL
```

- **Domain** (`backend/app/domain`): `TicketWorkflow` state machine, entities and domain exceptions. No framework code.
- **Services** (`backend/app/services`): use cases (create, transition, comment, assign) and notifications.
- **Repositories** (`backend/app/repositories`): MySQL access; every write calls a stored procedure.
- **API** (`backend/app/api`): routers, Pydantic schemas and dependency wiring. Controllers contain no business logic.
- **Database** (`db/`): schema, stored procedures and seed data, applied automatically at startup.

Full documentation:

- [Architecture diagram and decisions](docs/architecture.md)
- [Sequence diagrams: create ticket + status transition](docs/sequence-diagram.md)
- [Data model / ERD](docs/data-model.md)
- [Interface prototype (screens)](docs/mockup.md)
- Exported diagrams (PNG + PDF): [summary](docs/diagrams/summary) · [detailed](docs/diagrams/detailed)

## Workflow rules

| From | To | Requirement |
|---|---|---|
| PENDING | IN_PROGRESS | — |
| PENDING | RESOLVED | Diagnosis |
| IN_PROGRESS | PENDING | Comment (reason for putting it on hold) |
| IN_PROGRESS | RESOLVED | Diagnosis |
| RESOLVED | IN_PROGRESS | Comment (reason for reopening) |
| RESOLVED | CLOSED | — |

Any other transition returns `409 INVALID_TRANSITION`. A missing diagnosis or comment returns `422 BUSINESS_RULE_VIOLATION`. A diagnosis already stored on the ticket is reused when it is resolved again.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | API and database health check |
| GET | `/api/workflow` | Statuses and allowed transitions |
| GET | `/api/tickets?status=&operator_id=&created_from=&created_to=` | List tickets with filters |
| POST | `/api/tickets` | Create a ticket |
| GET | `/api/tickets/{id}` | Ticket with its full history |
| GET | `/api/tickets/{id}/history` | Ticket history only |
| POST | `/api/tickets/{id}/transitions` | Change status (`to_status`, `actor`, optional `diagnosis`, `comment`) |
| POST | `/api/tickets/{id}/comments` | Add a comment to the history |
| PUT | `/api/tickets/{id}/assignment` | Assign an operator |
| GET | `/api/operators` | List operators |
| GET | `/api/notifications?limit=` | Latest simulated notifications |

Error format:

```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "A diagnosis is required to move a ticket from PENDING to RESOLVED."
  }
}
```

## Running locally

### Option A: Docker Compose (recommended)

Requirements: Docker Desktop.

```bash
cp .env.example .env        # adjust passwords if you want
docker compose up --build
```

Open http://localhost:8000. The API docs are at http://localhost:8000/docs. The schema, stored procedures and demo data are applied automatically on startup.

### Option B: Run each part manually

Requirements: Python 3.12+, Node.js 20.19+ and a MySQL 8 server.

1. Create a database and a user, for example:

   ```sql
   CREATE DATABASE maintenance_tickets;
   CREATE USER 'tickets'@'%' IDENTIFIED BY 'change-me';
   GRANT ALL PRIVILEGES ON maintenance_tickets.* TO 'tickets'@'%';
   ```

2. Backend:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   export DATABASE_URL="mysql://tickets:change-me@localhost:3306/maintenance_tickets"
   export CORS_ORIGINS="http://localhost:5173"
   python -m app.db.migrate           # schema + stored procedures + seed
   uvicorn app.main:app --reload --port 8000
   ```

3. Frontend (in another terminal):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Open http://localhost:5173. Vite proxies `/api` to `http://localhost:8000` (override with `VITE_PROXY_TARGET`). To call a different API from a static build, set `VITE_API_URL` at build time.

### Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | `mysql://user:password@host:port/database`. Falls back to `MYSQL_URL` (provided by Railway). |
| `CORS_ORIGINS` | Comma-separated origins allowed to call the API (only needed when the frontend runs on another origin). |
| `MAINTENANCE_TEAM_EMAIL` | Recipient for notifications of unassigned tickets. |
| `PORT` | HTTP port inside the container (set by Railway). |

## Tests

```bash
cd backend
pytest
```

The suite covers the state machine (valid and invalid transitions, required diagnosis/comment), the service layer with in-memory repositories, the HTTP contract and error codes, the SQL script parser, and a consistency check between the domain rules and the transitions seeded in the database.

## Deployment (Railway)

1. Create a Railway project and add the **MySQL** plugin.
2. Add a service from this GitHub repository. Railway detects `railway.json` and builds the `Dockerfile`.
3. In the service variables, set `DATABASE_URL` to `${{MySQL.MYSQL_URL}}`.
4. Generate a public domain in the service settings.

On every deploy the container runs `python -m app.db.migrate` (idempotent) and then starts Uvicorn. The health check uses `/api/health`.

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/            # routers, schemas, dependency wiring
│   │   ├── core/           # settings, database connection, error handlers
│   │   ├── db/             # migration runner
│   │   ├── domain/         # state machine, models, exceptions, ports
│   │   ├── repositories/   # MySQL repositories (stored procedure calls)
│   │   └── services/       # ticket and notification use cases
│   └── tests/
├── db/                     # schema, stored procedures, seed data
├── docs/                   # architecture, sequence, data model, mockups
├── frontend/               # React + TypeScript + Vite
├── Dockerfile
├── docker-compose.yml
└── railway.json
```

## Requirements coverage

| Code | Where |
|---|---|
| R2.1 Frontend form + status board | `frontend/src/components/NewTicketForm.tsx`, `TicketBoard.tsx` |
| R2.2 Valid transitions (state machine) | `backend/app/domain/workflow.py`, `db/03_seed.sql` (`ticket_status_transitions`) |
| R2.3 Invalid transitions blocked | `TicketWorkflow.validate`, `sp_transition_ticket_status` |
| R2.4 1–N integrity Ticket ↔ History | `db/01_schema.sql` (`fk_history_ticket`, `ON DELETE RESTRICT`) |
| R2.5 Stored procedures | `db/02_stored_procedures.sql` |
| R2.6 Persisted history | `ticket_history` table, history timeline in the ticket drawer |
| R2.7 Separation of concerns | Layered backend (`api` / `services` / `domain` / `repositories`) |
| R2.8 Sequence analysis | [docs/sequence-diagram.md](docs/sequence-diagram.md) |
| R2.9 ERD | [docs/data-model.md](docs/data-model.md) |
| R2.10 Public URL | See **Live demo** above |
| R2.11 Source code | This repository (frontend, backend, stored procedures) |
| R2.12 README and code in English | This file and the whole codebase |
| Bonus | Assignment, filters, simulated notifications |
