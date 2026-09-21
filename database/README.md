# CloudVault Database

CloudVault uses PostgreSQL for application metadata.

## Main entities

- users
- folders
- files
- share_links

Actual file contents are stored in object storage, not PostgreSQL.

## Migration Tool

Alembic will manage schema migrations.
