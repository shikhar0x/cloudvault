# CloudVault — Architecture

## 1. Architectural Goal

CloudVault uses a **modular monorepo** containing a separate frontend application and backend application.

The architecture must remain simple enough for a 3-person college team while maintaining clear boundaries between:

- UI.
- API.
- business modules.
- authentication.
- database access.
- object storage.
- infrastructure.

The architecture must be extensible without prematurely introducing microservices.

---

## 2. Repository Architecture

```text
cloudvault/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── files/
│   │   │   ├── folders/
│   │   │   ├── sharing/
│   │   │   └── storage/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── services/
│   │   └── types/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── files/
│   │   │   ├── folders/
│   │   │   ├── sharing/
│   │   │   └── storage/
│   │   ├── database/
│   │   ├── infrastructure/
│   │   │   └── storage/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── infrastructure/
│   ├── docker/
│   └── aws/
│
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

This is a monorepo even though the top-level applications are named `frontend` and `backend`.

---

## 3. High-Level System Architecture

```text
                    ┌─────────────────────┐
                    │      Browser        │
                    │  Next.js Frontend   │
                    └──────────┬──────────┘
                               │ HTTPS / REST
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       ┌───────────┐     ┌────────────┐    ┌─────────────┐
       │   Auth    │     │ PostgreSQL │    │   Storage   │
       │  Module   │     │  Metadata  │    │   Service   │
       └───────────┘     └────────────┘    └──────┬──────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   AWS S3    │
                                            │ File Objects│
                                            └─────────────┘
```

---

## 4. Dependency Direction

The intended dependency direction is:

```text
Frontend
   |
   v
Backend API
   |
   +----> Business Modules
   |          |
   |          +----> Database
   |          |
   |          +----> Infrastructure
   |
   v
External Services
```

The frontend must not directly access:

- PostgreSQL.
- SQLAlchemy models.
- AWS credentials.
- S3 using server-side credentials.

The backend is the control boundary.

---

## 5. Frontend Architecture

The frontend uses feature-based modular organization.

```text
frontend/src/
├── app/
├── features/
│   ├── auth/
│   ├── files/
│   ├── folders/
│   ├── sharing/
│   └── storage/
├── components/
├── hooks/
├── lib/
├── services/
└── types/
```

### `app/`

Application routes and page composition.

### `features/`

Business features.

Example:

```text
features/files/
├── components/
├── hooks/
├── api.ts
├── types.ts
└── index.ts
```

### `components/`

Reusable UI components that are not tied strongly to one feature.

### `services/`

API client and cross-feature communication.

### `lib/`

Generic frontend utilities.

---

## 6. Backend Architecture

The backend is organized by business capability.

```text
backend/app/
├── core/
├── modules/
│   ├── auth/
│   ├── files/
│   ├── folders/
│   ├── sharing/
│   └── storage/
├── database/
├── infrastructure/
│   └── storage/
└── main.py
```

Each business module should normally contain:

```text
router.py
service.py
schemas.py
```

Models may live with the module or in the database model layer depending on the final implementation.

### Router

Responsible for:

- HTTP methods.
- Path parameters.
- Request/response handling.
- Dependency injection.

### Service

Responsible for:

- Business rules.
- Ownership checks.
- Calling repositories/database operations.
- Calling storage abstractions.

### Schemas

Responsible for:

- Input validation.
- Output serialization.

---

## 7. Core Layer

`backend/app/core/` contains application-wide concerns:

```text
core/
├── config.py
├── security.py
└── dependencies.py
```

Examples:

- Environment configuration.
- JWT configuration.
- Password hashing utilities.
- Authentication dependencies.
- Global application settings.

Business-specific logic must not be placed here merely because it is convenient.

---

## 8. Database Architecture

Runtime database code:

```text
backend/app/database/
├── session.py
├── base.py
└── models/
```

Project-level database lifecycle:

```text
database/
├── migrations/
└── seeds/
```

Technology:

- PostgreSQL.
- SQLAlchemy 2.x.
- Alembic.

Relationships:

```text
users
  |
  +----< folders
  |
  +----< files
             |
             +----< share_links
```

Folders support nesting:

```text
folders
   |
   +---- parent_folder_id
```

---

## 9. Object Storage Architecture

File content must not be stored directly inside PostgreSQL.

Use:

```text
PostgreSQL
    |
    | metadata
    v
files table

AWS S3
    |
    | binary content
    v
object
```

The `files.object_key` identifies the S3 object.

Example:

```text
users/{user_id}/folders/{folder_id}/{unique_file_id}-{filename}
```

The exact key convention may be adjusted during implementation.

---

## 10. Storage Abstraction

The backend must avoid coupling file-management business logic directly to boto3/S3 calls.

Use:

```text
backend/app/infrastructure/storage/

interface.py
s3.py
local.py
```

Conceptually:

```text
File Service
     |
     v
StorageProvider
     |
     +-----------> LocalStorage
     |
     +-----------> S3Storage
```

Development may use local storage where appropriate.

Production/cloud demonstration uses S3.

This allows storage implementation changes without rewriting the file module.

---

## 11. Authentication Architecture

```text
Register
   |
   v
Password hashing
   |
   v
PostgreSQL
```

Login:

```text
Email + Password
       |
       v
Verify hash
       |
       v
Generate JWT
       |
       v
Frontend
```

Protected request:

```text
Frontend
   |
   | Authorization: Bearer <token>
   v
FastAPI
   |
   v
JWT validation
   |
   v
Current user
   |
   v
Business operation
```

JWT payload should contain only the minimum information required, such as the user identifier and token metadata.

---

## 12. Authorization

Authentication answers:

> Who is the user?

Authorization answers:

> Is this user allowed to access this resource?

Every protected file/folder operation must verify ownership.

Example:

```text
GET /files/42
       |
       v
Authenticate user
       |
       v
Find file 42
       |
       v
file.user_id == current_user.id ?
       |
    ┌──┴──┐
   YES    NO
    |      |
 Allow    403
```

Do not rely only on frontend hiding.

Authorization must be enforced by the backend.

---

## 13. Sharing Architecture

Sharing uses a random token rather than exposing internal database IDs as the share credential.

```text
Owner
  |
  v
POST /api/shares
  |
  v
Generate secure token
  |
  v
Store token + file_id + expires_at
  |
  v
Return share URL
```

Public access:

```text
GET /api/shares/{token}
        |
        v
Find token
        |
        v
Check expiry
        |
   ┌────┴────┐
 Valid      Expired
   |           |
   v           v
Allow        Reject
```

---

## 14. File Upload Flow

```text
User selects file
        |
        v
Frontend
        |
        | multipart/form-data
        v
FastAPI
        |
        +---- validate user
        |
        +---- validate file
        |
        v
StorageProvider
        |
        v
AWS S3
        |
        v
Create metadata record
        |
        v
PostgreSQL
        |
        v
Return file metadata
```

Implementation must consider failure ordering so that database metadata and cloud objects do not become inconsistent.

---

## 15. File Download Flow

Authenticated download:

```text
User
 |
 v
Frontend
 |
 v
GET /files/{id}/download
 |
 v
Authenticate
 |
 v
Authorize ownership
 |
 v
Find object_key
 |
 v
StorageProvider
 |
 v
S3
 |
 v
Download/stream response
```

For public sharing:

```text
Share token
    |
    v
Validate token
    |
    v
Validate expiry
    |
    v
Find file
    |
    v
StorageProvider
    |
    v
Download
```

---

## 16. Storage Usage

The initial implementation should calculate usage from file metadata:

```text
SUM(files.file_size)
WHERE files.user_id = current_user
```

The result is exposed through:

```text
GET /api/storage/usage
```

The dashboard displays:

```text
Used: 2.4 GB
Total: 10 GB
```

The quota is an application-level limit for the mini project.

---

## 17. API Boundary

Frontend communicates with backend only through documented API contracts.

Example:

```text
POST /api/files/upload
GET  /api/files
GET  /api/files/{id}/download
DELETE /api/files/{id}
```

The frontend must not depend on internal backend files or database structures.

---

## 18. Local Development Architecture

Recommended local environment:

```text
Docker Compose
│
├── PostgreSQL
│
└── optional supporting services
```

Frontend:

```text
npm run dev
```

Backend:

```text
uvicorn app.main:app --reload
```

AWS S3 may be used directly during development if credentials/configuration are available. A local storage provider should remain available for development/testing where practical.

---

## 19. Deployment Architecture

Initial target:

```text
                  Internet
                     |
             ┌───────┴────────┐
             │                │
             v                v
        Frontend          Backend API
                               |
                 ┌─────────────┼─────────────┐
                 v             v             v
             PostgreSQL       S3          Auth logic
```

The exact hosting provider may be selected later.

Do not make deployment provider-specific decisions before the local application is stable.

---

## 20. Testing Architecture

Backend tests should cover:

- Registration.
- Login.
- Protected routes.
- Ownership checks.
- File metadata operations.
- Folder operations.
- Share token generation.
- Expired-link rejection.
- Storage operations.

Frontend testing should focus on critical user flows:

- Login.
- Upload.
- File listing.
- Folder navigation.
- Sharing.
- Logout.

Integration testing should verify:

```text
Frontend
   ↓
API
   ↓
Database
   ↓
Storage
```

---

## 21. Architectural Principles

1. Modular monolith first.
2. No microservices unless a concrete requirement appears.
3. Business logic belongs in services/modules.
4. Routers/controllers remain thin.
5. Frontend never accesses the database directly.
6. S3 access goes through a storage abstraction.
7. Authentication and authorization are enforced server-side.
8. Database stores metadata; object storage stores file content.
9. Infrastructure is separated from application code.
10. Keep the architecture understandable to a 3-person team.
