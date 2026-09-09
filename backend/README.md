# Qahwa 🎮

**Qahwa** is a host-controlled quiz challenge game backend — think of a live trivia game show engine where one Host manages the entire session while two competitors answer questions across categories and difficulty levels.

Built as a full production-style backend project: designed from requirements through deployment, with a clean service-layer architecture, full JWT authentication, tested business logic, and a fully containerized development environment.

---

## How the Game Works

- One **Host** controls the entire game — competitors never interact with the platform directly.
- The Host selects **4 topics** from a shared question bank.
- Each of the 2 players gets **12 questions** (4 topics × 3 difficulty levels: 100 / 300 / 500), drawn randomly so no two players ever get the same question.
- The Host opens a question, reveals the answer, and judges who answered correctly (or nobody).
- The session automatically finishes once all 24 questions have been judged — no manual "end game" step required.
- Scores are always **computed live** from judged questions (plus optional manual ±100 adjustments) — never stored as a mutable counter, so there's a single source of truth at all times.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language / Framework | Python, Django, Django REST Framework |
| Database | PostgreSQL (via [Supabase](https://supabase.com) in production) |
| Cache | Redis (via [Upstash](https://upstash.com) in production) |
| Auth | JWT (`djangorestframework-simplejwt`) |
| API Docs | Swagger UI (`drf-spectacular`) |
| Containerization | Docker & Docker Compose |
| Profiling (dev only) | `django-silk` |
| Hosting | [Render](https://render.com) (backend) |

---

## Architecture Highlights

This project follows a **Service Layer pattern**: business logic lives in `services.py` files, completely decoupled from HTTP. Views are intentionally "dumb" — they translate HTTP requests into service calls and back into responses. This means the core game logic (random question drawing, scoring, session lifecycle) can be tested and reused independently of Django REST Framework.

Key design decisions:

- **Bank vs. Session separation** — permanent content (Categories, Topics, Questions) is fully decoupled from ephemeral gameplay state (Sessions, Players, SessionQuestions). A `SessionQuestion` references a bank `Question` without ever mutating it.
- **UUID public identifiers** — internal auto-incrementing IDs are never exposed via the API; every externally-facing resource (`Session`, `SessionQuestion`) uses a separate `public_id` (UUID) to prevent enumeration attacks.
- **Database-level integrity** — critical rules like "one active session per host" are enforced with a PostgreSQL **partial unique index**, not just application code, so the guarantee holds even under race conditions or direct DB access.
- **Score as a derived value** — no stored `score` column. Scores are computed on demand by summing judged questions, plus a separate `manual_adjustment` field for host corrections — keeping a single source of truth and avoiding drift.
- **Automatic session completion** — `finish_session()` is triggered internally the moment the last question is judged, rather than relying on a client to call an "end game" endpoint.

---

## Project Structure

```
Qahwa/
├── apps/
│   ├── accounts/     # Custom Host user model
│   ├── bank/         # Categories, Topics, Questions, Answers, Media
│   └── game/         # Sessions, Players, SessionQuestions, game engine
├── core/              # Shared exceptions, constants, permissions
├── config/
│   └── settings/      # base / dev / prod split settings
├── requirements/       # base / dev / prod dependency sets
├── Dockerfile
└── docker-compose.yml
```

---

## API Overview

Full interactive documentation is available via Swagger UI at `/api/docs/` once the server is running.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain JWT access/refresh tokens |
| `POST` | `/api/token/refresh/` | Refresh an access token |
| `GET` | `/api/topics/` | List topics ready to play (filterable, searchable) |
| `POST` | `/api/sessions/` | Start a new game session |
| `GET` / `DELETE` | `/api/sessions/current/` | Get or abandon the host's active session |
| `GET` | `/api/sessions/{id}/questions/` | List all 24 questions for a session |
| `GET` | `/api/sessions/{id}/scoreboard/` | Get live scores |
| `POST` | `/api/session-questions/{id}/open/` | Open a question |
| `POST` | `/api/session-questions/{id}/judge/` | Judge a question's winner |
| `POST` | `/api/players/{id}/adjust-score/` | Apply a manual ±100 score adjustment |

All endpoints (except token issuance) require a valid JWT and enforce strict per-host data isolation — a host can never access another host's sessions.

---

## Running Locally with Docker

```bash
git clone https://github.com/elm0hamady/Qahwa.git
cd Qahwa
cp .env.example .env   # fill in your own values
docker-compose up --build
```

Then, in a separate terminal:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

The API will be available at `http://localhost:8000/api/`, with interactive docs at `http://localhost:8000/api/docs/`.

---

## Running Tests

```bash
python manage.py test apps.game.tests
```

Test coverage focuses on the core service layer: session validation, the random question-drawing logic, question state transitions, and the automatic session-completion trigger.

---

## Author

**Mohamed Elmohamady**
[GitHub](https://github.com/elm0hamady) · [LinkedIn](https://www.linkedin.com/in/elm0hamady/)
