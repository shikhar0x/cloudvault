# CloudVault Database

PostgreSQL stores **metadata only** — file contents live in AWS S3.

```text
backend/app/database/    runtime code (models, session management)
database/migrations/     Alembic schema migrations
database/seeds/          development demo data
docs/database/           database design documentation (ER diagram)
```

## Main entities

- `users`
- `folders` (self-referencing for nesting)
- `files` (metadata only)
- `share_links`

Relationships:

```text
User
 ├──< Folder ──< Folder (nested)
 ├──< File ──< ShareLink
 └── (files may reference a folder)
```

See `docs/database/database-design.md` for the full design.

## Command sequence (from a clean database)

```bash
# 1. Start PostgreSQL (Docker)
docker compose up -d postgres

# 2. Configure the connection (once)
cp .env.example .env   # then edit DATABASE_URL if needed

# 3. Create the schema from migrations
cd database/migrations
alembic upgrade head

# 4. (optional) seed demo data
cd ../..
bash scripts/seed.sh
```

## Test database

The backend test suite runs against a dedicated test database
(`cloudvault_test`, created automatically by `docker compose` or by the test
suite itself). The suite refuses to run against any database whose name does
not contain "test".
