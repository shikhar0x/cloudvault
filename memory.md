# CloudVault — AI Project Memory

## 1. Project Identity

**Project Name:** CloudVault

**Project Type:** College Mini Project

**Domain:** Cloud Computing / Web Application

**Core Idea:** A mini Google Drive-style cloud file storage and sharing platform.

CloudVault allows authenticated users to upload, organize, download, delete, and share files using temporary links.

---

# 2. Current Project Status

Status: **Implementation in progress**

No production implementation should be assumed to exist unless verified directly in the current repository.

The repository structure, requirements, architecture, rules, and development phases are being established before implementation.

## Member 3 status (Authentication + Database + Sharing)

Last verified: 2026-09-21 (test suite: 107 passed — see `backend/tests/`).

```text
DATABASE            IMPLEMENTED + VERIFIED
├── PostgreSQL connection (backend/app/database/session.py)   VERIFIED
├── SQLAlchemy 2.x models (users/folders/files/share_links)   VERIFIED
├── Alembic migrations (database/migrations, revision 46d1a57b07cf)  VERIFIED
├── dev seeds (database/seeds/seed.py)                        VERIFIED
└── composite FK prevents cross-user parent folders           VERIFIED

AUTHENTICATION       IMPLEMENTED + VERIFIED
├── POST /api/auth/register (Argon2id, 409 on duplicate)      VERIFIED
├── POST /api/auth/login (anti-enumeration timing)            VERIFIED
├── GET /api/auth/me (JWT-protected)                          VERIFIED
├── JWT HS256 w/ exp+sub required, alg pinned                 VERIFIED
└── get_current_user dependency (core/dependencies.py)        VERIFIED

AUTHORIZATION        IMPLEMENTED + VERIFIED
├── ensure_resource_owner helper (403 convention)             VERIFIED
└── JWT identity never overridable by request body            VERIFIED

SHARING              IMPLEMENTED + VERIFIED
├── POST /api/shares (ownership-checked, secure token)        VERIFIED
├── GET /api/shares/{token} (public, safe fields only)        VERIFIED
├── GET /api/shares/{token}/download (storage boundary)       VERIFIED*
├── expiry: 1h/1d/7d, server-side, 410 Gone when expired      VERIFIED
└── share_links.file_id ON DELETE CASCADE (no stale links)    VERIFIED

* Download endpoint validates token/expiry and delegates to Member 1's
  storage provider; returns 501 until app/infrastructure/storage exists
  (expected integration point, not a Member 3 gap).

NOT IMPLEMENTED (other members, intentionally untouched):
- files/folders/storage modules and S3 (Member 1)
- frontend (Member 2)
```

---

# 3. Current Authoritative Documents

The project currently uses:

```text
prd.md
architecture.md
rules.md
phases.md
memory.md
```

These documents define the intended project.

However, once implementation begins:

```text
CURRENT SOURCE CODE
        >
CURRENT TESTS
        >
CURRENT DATABASE/API STATE
        >
PROJECT DOCUMENTATION
```

The AI must inspect the actual repository before claiming implementation status.

---

# 4. Repository Decision

The project uses a modular monorepo.

Top-level structure:

```text
cloudvault/
├── frontend/
├── backend/
├── database/
├── infrastructure/
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Do not replace this with an `apps/web` / `apps/api` structure unless explicitly instructed.

---

# 5. Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic

## Database

- PostgreSQL

## Authentication

- JWT
- Argon2id or bcrypt password hashing

## Cloud Storage

- AWS S3

## Development

- Git
- GitHub
- Docker
- Docker Compose

Optional technologies must not be introduced without a concrete reason.

---

# 6. Core Features

Required:

```text
Authentication
├── Register
├── Login
└── Logout

Files
├── Upload
├── List
├── Download
└── Delete

Folders
├── Create
├── List
└── Navigate

Sharing
├── Generate link
├── Set expiry
├── Open public link
└── Download through link

Storage
└── Usage calculation
```

---

# 7. Cloud Architecture

The intended architecture is:

```text
Browser
   |
   v
Next.js Frontend
   |
   | REST API
   v
FastAPI Backend
   |
   ├──────────────> PostgreSQL
   |                  |
   |                  └── metadata
   |
   └──────────────> StorageProvider
                         |
                         └── AWS S3
                              |
                              └── file content
```

Database stores metadata.

S3 stores actual file objects.

---

# 8. Backend Modules

The backend should use a modular monolith:

```text
backend/app/modules/
├── auth/
├── files/
├── folders/
├── sharing/
└── storage/
```

Expected module pattern:

```text
router.py
service.py
schemas.py
```

Additional files are allowed when justified.

---

# 9. Storage Abstraction

Expected:

```text
backend/app/infrastructure/storage/
├── interface.py
├── local.py
└── s3.py
```

Business logic should depend on the storage interface rather than directly on boto3.

Local storage can support development/testing.

AWS S3 is the cloud implementation.

---

# 10. Database Model

Initial entities:

```text
users
folders
files
share_links
```

Basic relationships:

```text
User
 ├── Folders
 └── Files
       └── Share Links

Folder
 └── child Folders
```

A file contains metadata such as:

```text
id
user_id
folder_id
file_name
object_key
file_size
mime_type
created_at
```

Exact schema can evolve after implementation review.

---

# 11. Team Responsibilities

## Member 1 — Backend + Cloud

Owns primarily:

```text
backend/modules/files/
backend/modules/folders/
backend/modules/storage/
backend/infrastructure/storage/
infrastructure/aws/
```

Main responsibilities:

- FastAPI.
- File APIs.
- Folder APIs.
- Storage abstraction.
- S3 integration.
- Backend deployment.

---

## Member 2 — Frontend

Owns:

```text
frontend/
```

Main responsibilities:

- Next.js.
- UI/UX.
- Authentication screens.
- Dashboard.
- File browser.
- Upload/download/delete UI.
- Folder UI.
- Sharing UI.
- Storage usage UI.
- Frontend/API integration.

---

## Member 3 — Authentication + Database + Sharing

Owns primarily:

```text
backend/modules/auth/
backend/modules/sharing/
backend/database/
database/
```

Main responsibilities:

- PostgreSQL.
- SQLAlchemy.
- Alembic.
- Registration.
- Login.
- JWT.
- Password hashing.
- Authorization support.
- Share links.
- Expiry.

---

# 12. Academic Assessment Context

The project needs evidence for two formative assessments.

## FA1

Required:

```text
1. Frontend/UI development
2. Database Design
```

## FA2

Required:

```text
1. Backend implementation
2. Database integration
```

The implementation should therefore deliberately produce screenshots/evidence for these areas.

Do not postpone evidence collection until the final day.

---

# 13. Important Architectural Decisions

### Decision 1

Use a modular monolith.

Not microservices.

### Decision 2

Use `frontend/` and `backend/` as top-level applications.

### Decision 3

Use PostgreSQL for metadata.

### Decision 4

Use AWS S3 for actual file content.

### Decision 5

Use JWT authentication.

### Decision 6

Use feature-based frontend organization.

### Decision 7

Use business-module-based backend organization.

### Decision 8

Use a storage abstraction so local development does not require every operation to be tightly coupled to S3.

### Decision 9

Keep infrastructure separate from application code.

---

# 14. Scope Boundaries

Not currently part of the project:

- Real-time collaboration.
- File versioning.
- Desktop sync.
- Mobile app.
- AI features.
- Payment systems.
- Enterprise RBAC.
- Full-text document indexing.
- End-to-end encryption.
- Large-scale distributed architecture.

Do not add these without explicit approval.

---

# 15. Development Philosophy

The project should be developed:

```text
Small step
   ↓
Verify
   ↓
Integrate
   ↓
Test
   ↓
Document
   ↓
Next step
```

The AI must not attempt to implement the entire application in one pass.

---

# 16. AI Working Rules Summary

The AI must:

- Inspect current code before editing.
- Treat current source as implementation truth.
- Preserve working behavior.
- Avoid unnecessary rewrites.
- Work one logical step at a time.
- Keep commands copy-pasteable.
- Test changes.
- Never fabricate results.
- Never fabricate credentials.
- Never claim unverified deployment status.
- Avoid scope drift.
- Avoid unnecessary dependencies.
- Ask before major architectural changes.

---

# 17. Current Development Order

The intended order is:

```text
1. Repository setup
2. Backend/frontend foundations
3. Database foundation
4. Authentication
5. File/folder management
6. S3 integration
7. Sharing + expiry
8. Storage usage
9. Integration hardening
10. Deployment
11. Academic evidence
12. Final documentation/demo
```

---

# 18. Definition of Complete

CloudVault is complete when a user can:

```text
Register
  ↓
Login
  ↓
Create folder
  ↓
Upload file
  ↓
See file
  ↓
Download file
  ↓
Delete file
  ↓
Generate share link
  ↓
Set expiry
  ↓
Share link with another person
  ↓
Download through valid link
  ↓
Attempt expired link
  ↓
Receive access rejection
```

and the system demonstrates:

```text
Frontend
+
Backend API
+
Authentication
+
PostgreSQL
+
AWS S3
+
Cloud sharing
+
Expiry
```

---

# 19. Memory Maintenance Rule

This file is a project memory, not a substitute for inspecting the repository.

When implementation changes an important architectural decision, update this memory.

Do not record guesses as facts.

Use explicit states where useful:

```text
PLANNED
IMPLEMENTED
VERIFIED
BLOCKED
DEPRECATED
```

A feature should not be marked `IMPLEMENTED` merely because code was written; it should be marked `VERIFIED` only after appropriate testing.
