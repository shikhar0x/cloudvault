# Alembic Migrations

Schema lifecycle for CloudVault. The migration environment reads the same
`DATABASE_URL` as the application (environment variable first, then the app
settings / `.env`), so migrations always target the database the app uses.

## Commands

Run from this directory (`database/migrations/`):

```bash
alembic upgrade head       # apply all migrations (creates the full schema)
alembic current            # current revision
alembic history            # revision history
alembic downgrade base     # remove everything
alembic revision --autogenerate -m "description"   # after changing models
```

## Initial migration

`46d1a57b07cf` creates `users`, `folders`, `files`, `share_links` with:

- primary keys (UUID)
- foreign keys with explicit `ON DELETE` behavior
- unique constraints (`users.email`, `folders(user_id, id)`, `share_links.token`)
- check constraints (`email = lower(email)`, `file_size >= 0`,
  `parent_folder_id <> id`)
- indexes on every foreign key and on the share token
- timezone-aware timestamps with server defaults

A clean database can be initialized entirely from migrations. This is
verified automatically by `backend/tests/test_migrations.py`, which also
checks that the ORM models match the migrated schema exactly.

## Workflow after model changes

1. Edit the models in `backend/app/database/models/`.
2. `alembic revision --autogenerate -m "..."`.
3. Review the generated migration.
4. `alembic upgrade head`.
5. Run the backend tests.
