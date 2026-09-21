# CloudVault — Product Requirements Document

## 1. Project Overview

**Project Name:** CloudVault  
**Project Type:** College Mini Project  
**Category:** Cloud Computing / Web Application  
**Architecture:** Modular Monorepo  
**Primary Goal:** Build a small Google Drive-style cloud file storage and sharing platform that demonstrates frontend development, backend APIs, authentication, database integration, cloud object storage, file sharing, and link expiry.

CloudVault allows authenticated users to upload, organize, download, delete, and share files through temporary links.

The project is intentionally scoped as a mini project. It must demonstrate the required cloud concepts without attempting to reproduce the full functionality of Google Drive.

---

## 2. Problem Statement

Users commonly need a simple way to store files remotely, organize them, and share them with other people without manually transferring files.

CloudVault provides a simplified cloud storage system in which:

- Files are stored in cloud object storage.
- File metadata is stored in a relational database.
- Users authenticate before accessing their private files.
- Files can be shared through generated links.
- Shared links can expire automatically.
- Users can view their storage usage.

---

## 3. Objectives

The project must demonstrate:

1. Frontend/UI development.
2. Backend REST API development.
3. User authentication.
4. Relational database design and integration.
5. Cloud object storage.
6. File upload/download/delete operations.
7. Folder organization.
8. Temporary file-sharing links.
9. Link expiry.
10. Storage usage calculation.
11. Modular software architecture.
12. Basic deployment readiness.
13. Testing and documentation.

---

## 4. Target Users

### Authenticated User

A normal CloudVault user who can:

- Register.
- Log in.
- Upload files.
- Create folders.
- Browse files/folders.
- Download files.
- Delete files.
- Generate sharing links.
- Set sharing-link expiry.
- View storage usage.

### Public Share Recipient

A person who receives a valid CloudVault sharing link.

They can:

- Open the shared link.
- View basic file information.
- Download the file while the link is valid.

They do not receive access to the owner's private dashboard.

---

## 5. Functional Requirements

### FR-01 — User Registration

The system shall allow a new user to create an account using:

- Name.
- Email.
- Password.

Passwords must never be stored in plaintext.

### FR-02 — User Login

The system shall authenticate registered users and issue an access token.

### FR-03 — Authentication

Protected operations shall require valid authentication.

At minimum, the following must be protected:

- File listing.
- File upload.
- File download.
- File deletion.
- Folder creation.
- Folder deletion.
- Sharing-link creation.
- Storage-usage information.

### FR-04 — File Upload

Authenticated users shall be able to upload files.

The system shall:

1. Receive the file through the backend.
2. Validate basic file metadata.
3. Store the file in object storage.
4. Store metadata in PostgreSQL.
5. Return the created file information.

### FR-05 — File Listing

Users shall be able to view files belonging to their account.

Users must never receive another user's private file metadata through normal authenticated APIs.

### FR-06 — File Download

Authenticated users shall be able to download their own files.

### FR-07 — File Deletion

Authenticated users shall be able to delete their own files.

Deletion must remove:

- The object from cloud storage.
- The corresponding metadata from the database.

The implementation must avoid leaving orphaned objects where practical.

### FR-08 — Folder Creation

Users shall be able to create folders.

Folders may support nesting through a parent-folder relationship.

### FR-09 — Folder Navigation

Users shall be able to browse files within a selected folder.

### FR-10 — Sharing Links

Users shall be able to generate a shareable link for a file.

A sharing link must use a non-guessable token.

### FR-11 — Link Expiry

Users shall be able to specify an expiry duration for a sharing link.

The backend must reject expired links.

### FR-12 — Public File Download

A valid public sharing link shall allow download of the associated file without exposing the owner's private dashboard.

### FR-13 — Storage Usage

The dashboard shall display storage usage based on file metadata.

Example:

`2.4 GB / 10 GB`

The quota is an application-level demonstration quota unless a real cloud quota is explicitly implemented.

### FR-14 — Error Handling

The application shall display useful errors for:

- Invalid credentials.
- Unauthorized access.
- Missing files.
- Invalid folders.
- Expired links.
- Upload failures.
- Database failures.
- Storage failures.

---

## 6. Non-Functional Requirements

### NFR-01 — Security

- Passwords must be hashed.
- Secrets must not be committed to Git.
- Protected APIs must validate authentication.
- Users must only access resources they own.
- Sharing tokens must be sufficiently unpredictable.
- AWS credentials must be provided through environment configuration or an equivalent secret-management mechanism.

### NFR-02 — Maintainability

The codebase must use feature/module-based organization.

Avoid large catch-all files such as:

- `utils.py` containing unrelated business logic.
- `services.py` containing every service.
- One giant frontend component.

### NFR-03 — Reliability

Database and object-storage failures must not silently produce inconsistent records.

### NFR-04 — Usability

The UI should be understandable to a first-time user.

### NFR-05 — Portability

The application should be runnable locally using documented setup instructions.

### NFR-06 — Testability

Core backend services and APIs should have automated tests.

---

## 7. Technology Stack

### Frontend — Required

- Next.js
- React
- TypeScript
- Tailwind CSS
- Fetch or Axios for API communication

### Backend — Required

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic

### Authentication — Required

- JWT-based authentication
- Secure password hashing using Argon2id or bcrypt

### Database — Required

- PostgreSQL

### Cloud Storage — Required

- AWS S3

### Development / Deployment

- Git
- GitHub
- Docker
- Docker Compose

### Optional / Only if justified

- AWS EC2 for backend deployment
- Vercel or AWS hosting for frontend
- AWS RDS for managed PostgreSQL
- Terraform for infrastructure-as-code

Do not introduce optional infrastructure merely to make the project look more complex.

---

## 8. Proposed Storage Model

The database stores metadata:

```text
users
folders
files
share_links
```

AWS S3 stores actual file objects.

Conceptually:

```text
Frontend
   |
   v
FastAPI
   |
   +----> PostgreSQL
   |       metadata
   |
   +----> AWS S3
           file objects
```

The database is the source of application metadata. S3 is the source of stored file content.

---

## 9. Initial Database Entities

### users

- id
- name
- email
- password_hash
- created_at

### folders

- id
- user_id
- parent_folder_id
- name
- created_at

### files

- id
- user_id
- folder_id
- file_name
- object_key
- file_size
- mime_type
- created_at

### share_links

- id
- file_id
- token
- expires_at
- created_at

Exact columns may evolve during implementation if required by the actual design.

---

## 10. API Scope

The initial API should cover:

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

POST   /api/files/upload
GET    /api/files
GET    /api/files/{id}
GET    /api/files/{id}/download
DELETE /api/files/{id}

POST   /api/folders
GET    /api/folders
DELETE /api/folders/{id}

POST   /api/shares
GET    /api/shares/{token}
GET    /api/shares/{token}/download

GET    /api/storage/usage
```

The exact API contract must be finalized before frontend/backend integration.

---

## 11. UI Scope

Minimum screens:

1. Login.
2. Register.
3. Dashboard.
4. File/folder browser.
5. Upload dialog.
6. Create-folder dialog.
7. Share dialog.
8. Public share page.
9. Basic profile/logout controls.

The dashboard should visibly demonstrate:

- Files.
- Folders.
- Upload.
- Download.
- Delete.
- Share.
- Storage usage.

---

## 12. Cloud Concepts Demonstrated

The final project must visibly demonstrate:

```text
Frontend
   |
   v
Backend API
   |
   +---- Authentication
   |
   +---- PostgreSQL
   |
   +---- Cloud Object Storage
```

Additional demonstrated concepts:

- Remote object storage.
- REST APIs.
- Authentication and authorization.
- Database persistence.
- Cloud file sharing.
- Expiring access.
- Containerized development/deployment.

---

## 13. Academic Assessment Alignment

### Formative Assessment 1

The project should provide evidence for:

1. Frontend/UI development.
2. Database design.

Evidence should include screenshots of:

- Login/register UI.
- Dashboard.
- File browser.
- Upload/folder/share interfaces.
- ER diagram.
- Database tables/schema.
- Relevant database records.

### Formative Assessment 2

The project should provide evidence for:

1. Backend implementation.
2. Database integration.

Evidence should include screenshots of:

- Running API.
- API endpoints/results.
- Authentication flow.
- File upload/download operations.
- Database records created through the application.
- Backend/database integration.

The development plan must intentionally create these evidence points rather than adding them after the project is finished.

---

## 14. Project Constraints

The project is a mini project, not a production replacement for Google Drive.

Out of scope unless explicitly added later:

- Real-time collaboration.
- File versioning.
- Google Drive/Dropbox synchronization.
- Desktop sync client.
- Mobile application.
- Advanced malware scanning.
- Full-text document search.
- Enterprise multi-tenancy.
- Complex role-based access control.
- End-to-end encryption.
- Large-scale distributed processing.

---

## 15. Definition of Done

CloudVault is considered complete when:

- A user can register and log in.
- Authenticated users can upload files.
- Uploaded files are stored in S3.
- File metadata is stored in PostgreSQL.
- Users can create and navigate folders.
- Users can download their files.
- Users can delete their files.
- Users can generate sharing links.
- Sharing links can expire.
- Expired links are rejected.
- Storage usage is displayed.
- Frontend and backend are integrated.
- Core functionality is tested.
- The application can be started using documented commands.
- Required academic screenshots/evidence can be produced.
- No secrets or local environment files are committed.

---

## 16. Guiding Principle

Build the smallest complete system that clearly demonstrates cloud file storage and sharing.

Do not add complexity unless it directly improves:

- functionality,
- security,
- maintainability,
- cloud demonstration,
- academic evaluation, or
- future extensibility.
