# CloudVault — Development Phases and Team Plan

## 1. Team

CloudVault is developed by 3 members.

### Member 1 — Backend + Cloud

Primary ownership:

- FastAPI backend.
- File APIs.
- Folder APIs.
- Storage service.
- AWS S3 integration.
- Backend deployment support.

### Member 2 — Frontend

Primary ownership:

- Next.js frontend.
- UI/UX.
- Dashboard.
- File browser.
- Upload/download/delete UI.
- Folder UI.
- Storage UI.
- API integration.

### Member 3 — Authentication + Database + Sharing

Primary ownership:

- PostgreSQL design.
- SQLAlchemy models.
- Alembic migrations.
- Registration/login.
- JWT authentication.
- Authorization support.
- Share links.
- Link expiry.
- Integration testing.

All members participate in final integration, testing, documentation, and presentation.

---

# 2. Development Strategy

The project follows:

```text
Requirements
    ↓
Architecture
    ↓
Database + API contracts
    ↓
Foundation
    ↓
Core features
    ↓
Integration
    ↓
Cloud integration
    ↓
Testing
    ↓
Deployment
    ↓
Academic evidence
```

Parallel work is encouraged where interfaces are already defined.

---

# Phase 0 — Project Setup and Contract

### Goal

Create the repository and establish rules before feature development.

### Member 1

- Set up backend project.
- Configure FastAPI.
- Create application entry point.
- Establish module structure.
- Create health endpoint.

### Member 2

- Set up Next.js + TypeScript.
- Configure Tailwind CSS.
- Create base layout.
- Create initial dashboard shell.
- Establish frontend feature structure.

### Member 3

- Design initial PostgreSQL schema.
- Set up SQLAlchemy.
- Set up Alembic.
- Create initial models/migration.
- Document ER relationships.

### Shared

- Create GitHub repository.
- Create branch strategy.
- Add `.gitignore`.
- Add `.env.example`.
- Create README.
- Agree on API naming conventions.

### Exit Criteria

```text
Frontend runs.
Backend runs.
Database connects.
Repository structure is established.
All three members can clone and run the project.
```

---

# Phase 1 — Authentication and Database Foundation

## Member 3 — Primary

Implement:

- User model.
- Registration.
- Password hashing.
- Login.
- JWT generation.
- Current-user endpoint.
- Authentication dependency.

Endpoints:

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

## Member 1 — Support

- Integrate authentication dependency with backend module structure.
- Establish protected-route pattern.

## Member 2 — Parallel

Build:

- Login page.
- Registration page.
- Auth state handling.
- Logout.
- Protected dashboard routing.

### Exit Criteria

```text
Register
   ↓
Login
   ↓
JWT
   ↓
Protected dashboard
```

works end-to-end.

---

# Phase 2 — File and Folder Foundation

## Member 1 — Primary

Implement:

- File module.
- Folder module.
- File metadata.
- File listing.
- Upload API.
- Download API.
- Delete API.
- Folder creation.
- Folder listing/navigation.
- Ownership checks.

## Member 3

- Finalize database relationships.
- Implement migrations.
- Validate ownership-related constraints.
- Support file/folder data model.

## Member 2

Build:

- File browser.
- Folder browser.
- Upload dialog.
- File cards/list.
- Download actions.
- Delete actions.
- Create-folder dialog.

### Exit Criteria

Users can manage files/folders through the application.

At this phase, local storage may be used if S3 is not yet integrated.

---

# Phase 3 — Cloud Object Storage

## Member 1 — Primary

Implement storage abstraction:

```text
StorageProvider
    ├── LocalStorage
    └── S3Storage
```

Integrate AWS S3.

Implement:

- Object upload.
- Object retrieval.
- Object deletion.
- Object key generation.
- Error handling.

## Member 3

- Verify database/S3 metadata consistency.
- Test ownership and file lifecycle.

## Member 2

- Connect frontend to final upload/download/delete APIs.
- Add upload progress/loading states where practical.
- Add useful error states.

### Exit Criteria

```text
Frontend
   ↓
FastAPI
   ↓
S3 + PostgreSQL
```

works for the core file lifecycle.

---

# Phase 4 — Sharing and Link Expiry

## Member 3 — Primary

Implement:

- Share link creation.
- Secure token generation.
- Expiry handling.
- Public share lookup.
- Public download.
- Expired-link rejection.

Endpoints:

```text
POST /api/shares
GET  /api/shares/{token}
GET  /api/shares/{token}/download
```

## Member 1

- Integrate sharing with storage provider.
- Ensure shared download retrieves the correct S3 object.
- Review security.

## Member 2

Build:

- Share dialog.
- Expiry selector.
- Generated-link display.
- Copy-link action.
- Public share page.
- Expired-link UI.

### Exit Criteria

```text
Upload
  ↓
Share
  ↓
Generate link
  ↓
Open link
  ↓
Download
  ↓
Expiry
  ↓
Access rejected
```

works.

---

# Phase 5 — Storage Usage and Dashboard

## Member 1

Implement:

```text
GET /api/storage/usage
```

and calculate storage usage from file metadata.

## Member 2

Implement:

- Storage usage card.
- Used/total display.
- File counts.
- Dashboard statistics.

## Member 3

Verify:

- Usage calculation.
- Database consistency.
- Edge cases after deletion.

### Exit Criteria

Dashboard shows meaningful storage information.

---

# Phase 6 — Integration and Hardening

All members participate.

## Member 1

Focus:

- Backend error handling.
- S3 failure handling.
- API validation.
- Backend tests.
- Performance sanity checks.

## Member 2

Focus:

- UI consistency.
- Loading states.
- Empty states.
- Error states.
- Responsive layout.
- API error handling.

## Member 3

Focus:

- Authentication tests.
- Authorization tests.
- Share-link security.
- Expiry tests.
- Database constraints.
- Integration tests.

### Shared Test Matrix

```text
Authentication
├── Register
├── Login
├── Invalid login
└── Protected endpoint

Files
├── Upload
├── List
├── Download
└── Delete

Folders
├── Create
├── List
└── Nested folders

Sharing
├── Generate
├── Access
├── Download
└── Expire

Storage
└── Usage calculation
```

---

# Phase 7 — Cloud Deployment

Do this only after the local system is stable.

## Member 1

Primary:

- AWS S3 final configuration.
- Backend deployment.
- Environment configuration.
- Cloud infrastructure.

## Member 2

- Production frontend configuration.
- API base URL.
- Production build.
- Deployment.

## Member 3

- Production database configuration.
- Migration execution.
- Security configuration review.
- Verify authentication and sharing.

### Exit Criteria

A demonstrable deployed version exists, if deployment is required for the submission.

---

# Phase 8 — Academic Evidence and Documentation

## Member 1

Collect:

- Backend/API screenshots.
- S3 evidence.
- Upload/download flow.
- Cloud architecture evidence.

## Member 2

Collect:

- Login.
- Register.
- Dashboard.
- File management.
- Folder UI.
- Share UI.
- Storage UI.

## Member 3

Collect:

- ER diagram.
- Database tables.
- Authentication evidence.
- API/database integration evidence.
- Sharing/expiry evidence.

### FA1 Evidence

```text
Frontend/UI
+
Database Design
```

### FA2 Evidence

```text
Backend Implementation
+
Database Integration
```

---

# 3. Suggested Timeline

For approximately 3 weeks:

| Phase | Time | M1 | M2 | M3 |
|---|---|---|---|---|
| Setup | Day 1–2 | Backend | Frontend | DB |
| Auth foundation | Day 3–5 | Support | Auth UI | Auth |
| Files/folders | Day 6–9 | Backend | UI | DB |
| S3 | Day 10–12 | S3 | Integration | Validation |
| Sharing | Day 13–15 | Storage support | Sharing UI | Sharing |
| Dashboard | Day 16 | Usage API | Dashboard | Validation |
| Hardening | Day 17–18 | Backend tests | UI testing | Security tests |
| Deployment | Day 19 | AWS | Frontend | DB |
| Evidence | Day 20–21 | Backend evidence | UI evidence | DB evidence |

The schedule can be compressed or expanded without changing ownership.

---

# 4. Git Workflow

Each member works primarily on a feature branch.

```text
main
│
├── member1/backend
├── member2/frontend
└── member3/auth-database
```

Prefer more specific branches for larger features:

```text
feat/file-upload
feat/dashboard
feat/jwt-auth
feat/share-links
```

Pull requests should be small enough to review.

---

# 5. Phase Completion Rule

A phase is not complete merely because code exists.

Each phase requires:

```text
Code
 ↓
Local verification
 ↓
Integration verification
 ↓
Tests
 ↓
Documentation/evidence
 ↓
Phase complete
```

---

# 6. Dependency Strategy

The team should work in parallel whenever possible.

Example:

```text
Member 3 defines auth API
            │
            ├───────────────┐
            ▼               ▼
       Member 3          Member 2
       backend            frontend
            │               │
            └───────┬───────┘
                    ▼
                Integration
```

Do not make the frontend wait for the entire backend.

Define contracts early and use mock data where appropriate.

---

# 7. Final Demonstration Flow

The final demo should follow one complete user journey:

```text
Register
   ↓
Login
   ↓
Dashboard
   ↓
Create folder
   ↓
Upload file
   ↓
File stored in S3
   ↓
Metadata stored in PostgreSQL
   ↓
View storage usage
   ↓
Generate share link
   ↓
Set expiry
   ↓
Open public link
   ↓
Download file
   ↓
Wait/force expiry
   ↓
Show expired-link rejection
```

This single flow demonstrates most of the project's important concepts.
