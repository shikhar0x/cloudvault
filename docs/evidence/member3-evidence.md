# Member 3 — Academic Evidence Guide (FA1 / FA2)

Member 3 owns **authentication + database + sharing**. This document lists the
evidence screenshots worth capturing, with the exact commands that produce
each state. Capture them as features become stable — do not wait for the end.

> Never fabricate screenshots. Every item below maps to a real, runnable
> command in this repository.

---

## FA1 — Database design

| Evidence | How to produce it |
|---|---|
| ER diagram | Render `docs/database/database-design.md` (Mermaid) on GitHub, or export the diagram to an image |
| Database schema/DDL | `psql $DATABASE_URL -c '\d+ users' -c '\d+ folders' -c '\d+ files' -c '\d+ share_links'` |
| Schema created purely by migrations | Run `cd database/migrations && alembic upgrade head` on an empty database, then screenshot `alembic current` + `\dt` |
| Migration history | `alembic history --verbose` |
| Constraints in action | Screenshot of the test run: `pytest backend/tests/test_database_models.py -v` (uniqueness, composite FK rejecting cross-user parents, cascades) |
| Seeded data (users/folders/files/shares) | `bash scripts/seed.sh` then `psql ... -c 'SELECT email, created_at FROM users;'` etc. |

## FA2 — Backend implementation & database integration

| Evidence | How to produce it |
|---|---|
| Running API | `cd backend && uvicorn app.main:app --reload`, open `http://localhost:8000/docs` (interactive Swagger UI) |
| Registration | `curl -X POST http://localhost:8000/api/auth/register -H 'Content-Type: application/json' -d '{"name":"Demo","email":"demo@example.com","password":"Sup3rSecret!"}'` |
| Duplicate email rejection (409) | Repeat the same curl command |
| Login returns JWT | `curl -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@example.com","password":"Sup3rSecret!"}'` |
| Passwords hashed in the database | `psql ... -c "SELECT email, left(password_hash, 30) FROM users;"` — show `$argon2id$...` |
| Protected endpoint works | `curl http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>"` |
| Protected endpoint rejects without token | `curl -i http://localhost:8000/api/auth/me` (401) |
| Share creation + URL | `curl -X POST http://localhost:8000/api/shares -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' -d '{"file_id":"<uuid>","expires_in":"1h"}'` |
| Public share lookup (no auth) | `curl http://localhost:8000/api/shares/<token>` |
| Expired link rejected (410) | Use the expired seed link, or wait out a `1h` link, then `curl -i http://localhost:8000/api/shares/<token>` |
| Ownership check (403) | Attempt `POST /api/shares` for another user's file (two accounts) |
| Ownership bypass attempt rejected | Same request with a forged `"user_id"` in the body — still 403/201 by JWT identity only |
| Full integration flow automated | `pytest backend/tests/test_integration_flow.py -v` |
| Whole Member 3 test suite | `cd backend && pytest tests/ -v` (all green) |

---

## Suggested demo narrative (maps to the final demonstration flow)

```text
Register  →  Login  →  /auth/me  →  share a file  →  open the public link
→  show the DB row (token + expires_at)  →  force/wait expiry  →  410 rejected
```

The seed script (`bash scripts/seed.sh`) pre-creates a valid **and** an
expired share link so the expiry rejection can be demonstrated instantly
without waiting.
