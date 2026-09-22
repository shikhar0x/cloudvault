# Database Seeds

Development-only demo data for CloudVault.

## What it creates

- 2 demo users (`alice@demo.cloudvault.local`, `bob@demo.cloudvault.local`)
- Nested folders (`Documents` → `Reports`, `Photos`)
- File **metadata** rows (no binary content — object storage would hold the bytes)
- Share links: one valid for 7 days, one already expired (to demo expiry rejection)

## Demo credentials

Development-only, intentionally public:

```text
email:    alice@demo.cloudvault.local
password: DemoPass123!
```

Passwords are stored as real Argon2id hashes. Never seed real credentials.

## Running

From the repository root (requires backend dependencies and `DATABASE_URL`
or a `.env` file):

```bash
python database/seeds/seed.py
```

Or via the helper script:

```bash
bash scripts/seed.sh
```

The script is idempotent (it skips when demo data already exists) and
refuses to run when `APP_ENV=production`.
