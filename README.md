# CloudVault

**CloudVault** is a modular cloud file storage and sharing platform built with FastAPI, PostgreSQL, AWS S3, and Next.js. It provides a secure, self-hosted alternative to cloud storage drives with end-to-end user authentication, folder hierarchy, drag-and-drop file management, and time-limited public sharing links.

---

## Architecture & Technology Stack

```text
┌─────────────────────────────────────────────────────────────┐
│                 Next.js Frontend (Port 3000)                │
│    - Modular Dark Frame UI & File Explorer                  │
│    - Global Drag & Drop File Upload                         │
│    - Keyboard Shortcuts (/, ⌘K, U, N, Esc)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API & Streaming
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8001)                 │
│    - JWT Authentication (Argon2id password hashing)         │
│    - Storage Provider (AWS S3 & Local filesystem fallback)  │
│    - File, Folder, Sharing & Storage Quotas APIs            │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│     PostgreSQL Database      │ │      Object Storage         │
│         (Port 5433)          │ │      (AWS S3 / Local)       │
│  - SQLAlchemy 2.x ORM        │ │  - Binary Chunk Streaming   │
│  - Alembic Migrations        │ │  - Automatic TTL Expiration │
└──────────────────────────────┘ └─────────────────────────────┘
```

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide Icons.
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.x, Argon2id, PyJWT.
- **Database:** PostgreSQL (with Alembic migrations and database seeds).
- **Storage:** Storage abstraction layer supporting AWS S3 and local disk streaming.
- **Development & Testing:** Docker, Docker Compose, Pytest (110 automated tests).

---

## Core Features

- **Authentication & Security:** User registration and login powered by Argon2id password hashing, signed JWT tokens, and strict ownership validation (`403 Forbidden` on unauthorized access).
- **Directory Hierarchy:** Create folders, organize nested subdirectories, and navigate using interactive breadcrumbs.
- **File Management:** Upload single or multiple files with drag-and-drop, stream downloads, inspect file metadata, and delete items with automatic storage object cleanup.
- **Time-Limited Public Sharing:** Generate secure share links with configurable expiry (1 hour, 24 hours, 7 days). Recipient portal allows direct downloading without account registration, automatically rejecting expired links (`410 Gone`).
- **Live Storage Quotas:** Dynamic calculation of storage usage, file counts, and quota meters.
- **Keyboard Shortcuts:**
  - <kbd>⌘K</kbd> or <kbd>/</kbd> — Focus & select search bar
  - <kbd>U</kbd> — Open file upload dialog
  - <kbd>N</kbd> — Open new folder dialog
  - <kbd>Esc</kbd> — Close active modal, inspector, or clear search

---

## Repository Structure

```text
cloudvault/
├── frontend/               # Next.js 15 TypeScript application
│   ├── src/
│   │   ├── app/            # App Router pages (Dashboard, Login, Register, Share)
│   │   ├── lib/            # API client and auth state helpers
│   │   └── types/          # TypeScript definitions
│   └── package.json
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── core/           # Security, JWT, configuration, dependencies
│   │   ├── database/       # SQLAlchemy Base, session, and ORM models
│   │   ├── infrastructure/ # Storage abstraction (local.py, s3.py)
│   │   ├── modules/        # Modular routers (auth, files, folders, sharing, storage)
│   │   └── main.py         # Application entrypoint
│   ├── tests/              # 110 automated pytest suites
│   └── requirements.txt
├── database/
│   ├── migrations/         # Alembic database migrations
│   └── seeds/              # Development seed scripts
├── docker-compose.yml      # Local PostgreSQL service configuration
├── prd.md                  # Product Requirements Document
├── architecture.md         # System Architecture specification
├── rules.md                # Development and coding standards
├── phases.md               # Team development phases
└── memory.md               # Project implementation memory
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) (v18+) & `npm`
- [Python](https://www.python.org/) (v3.10+)

---

### 2. Database Setup

Start the PostgreSQL container on port `5433`:
```bash
docker compose up -d postgres
```

Apply database migrations:
```bash
backend/.venv/bin/alembic upgrade head
```

Seed initial development data (users, folders, files, and demo share links):
```bash
backend/.venv/bin/python database/seeds/seed.py
```

---

### 3. Start the Backend API

Run the FastAPI backend on `http://127.0.0.1:8001`:
```bash
PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

- **Interactive API Documentation (Swagger):** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **Health Endpoint:** [http://127.0.0.1:8001/api/health/db](http://127.0.0.1:8001/api/health/db)

---

### 4. Start the Frontend Application

In a separate terminal, start the Next.js dev server on `http://localhost:3000`:
```bash
cd frontend
npm install
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## Demo Accounts

Pre-seeded credentials for testing:

| Email | Password | Role |
| :--- | :--- | :--- |
| `alice@demo.cloudvault.local` | `DemoPass123!` | Test User (with seeded folders & files) |
| `bob@demo.cloudvault.local` | `DemoPass123!` | Test User (with separate private drive) |

---

## Running Automated Tests

Run the complete test suite (110 passed test cases):
```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests
```

---

## Key API Endpoints

| Category | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **System** | `GET` | `/api/health/db` | PostgreSQL connectivity check |
| **Auth** | `POST` | `/api/auth/register` | Create a new user account |
| **Auth** | `POST` | `/api/auth/login` | Log in and receive signed JWT |
| **Auth** | `GET` | `/api/auth/me` | Fetch authenticated user profile |
| **Folders** | `POST` | `/api/folders` | Create a folder or subfolder |
| **Folders** | `GET` | `/api/folders` | List folders in the current path |
| **Folders** | `DELETE`| `/api/folders/{id}` | Delete folder and recursive items |
| **Files** | `POST` | `/api/files/upload` | Upload a file to storage and DB |
| **Files** | `GET` | `/api/files` | List files in current folder |
| **Files** | `GET` | `/api/files/{id}/download` | Stream file binary download |
| **Files** | `DELETE`| `/api/files/{id}` | Delete file from storage and DB |
| **Sharing** | `POST` | `/api/shares` | Create expiring share link (1h/1d/7d) |
| **Sharing** | `GET` | `/api/shares/{token}` | Public file metadata lookup |
| **Sharing** | `GET` | `/api/shares/{token}/download` | Public binary stream download |
| **Storage** | `GET` | `/api/storage/stats` | Storage quota & usage breakdown |

---

## Team Ownership

- **Member 1 (Backend + Cloud):** FastAPI modules, files/folders services, storage provider abstraction, S3 integration.
- **Member 2 (Frontend):** Next.js dashboard, modular dark frame UI, drag-and-drop, keyboard shortcuts, public share portal.
- **Member 3 (Auth, Database & Sharing):** PostgreSQL schema, SQLAlchemy models, Alembic migrations, JWT auth, expiring share links.

---

## License
MIT License &copy; CloudVault Project.
