# CloudVault

CloudVault is a modular cloud file storage and sharing platform developed as a college mini project.

## Architecture

- Frontend: Next.js + React + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Object Storage: AWS S3
- Authentication: JWT
- Development: Docker / Docker Compose

## Repository

```text
frontend/       Frontend application
backend/        Backend API
database/       Database migrations and seeds
infrastructure/ Cloud and deployment configuration
docs/           Technical documentation
scripts/        Development scripts
Project Documents
- prd.md — Product requirements
- architecture.md — System architecture
- rules.md — AI/development rules
- phases.md — Development phases and team ownership
- memory.md — AI project memory
Team
- Member 1 — Backend + Cloud
- Member 2 — Frontend
- Member 3 — Authentication + Database + Sharing
  EOF

---

# 16. Initial Docker Compose skeleton

Don't configure the entire production environment yet.

For now, create only PostgreSQL:

```bash
cat > docker-compose.yml <<'EOF'
services:
  postgres:
    image: postgres:16-alpine
    container_name: cloudvault-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: cloudvault
      POSTGRES_USER: cloudvault
      POSTGRES_PASSWORD: change_me
    ports:
      - "5432:5432"
    volumes:
      - cloudvault_postgres_data:/var/lib/postgresql/data

volumes:
  cloudvault_postgres_data:
