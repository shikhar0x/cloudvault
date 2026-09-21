# CloudVault — AI Development Rules

## 1. Purpose

This file defines the rules an AI coding agent must follow while developing CloudVault.

The goal is to prevent:

- scope drift,
- unnecessary redesign,
- uncontrolled dependency additions,
- architecture divergence,
- destructive changes,
- premature optimization,
- duplicated implementations,
- undocumented behavior changes.

These rules apply to every development session.

---

# 2. Source of Truth

The current repository is the primary source of truth for implementation status.

Priority order:

```text
1. Current source code
2. Current tests
3. Current database/schema state
4. Current API contracts
5. architecture.md
6. prd.md
7. phases.md
8. memory.md
9. Older discussion/context
```

If documentation conflicts with working code, inspect the repository and tests before changing behavior.

Do not assume a documented feature is implemented.

---

# 3. Project Scope

The core scope is:

- Authentication.
- File upload.
- File download.
- File deletion.
- Folder creation/navigation.
- PostgreSQL metadata.
- AWS S3 object storage.
- Shareable file links.
- Link expiry.
- Storage usage.
- Frontend/backend integration.

Do not add unrelated features.

Examples of scope drift:

- Chat.
- Social profiles.
- Real-time collaboration.
- File versioning.
- AI document analysis.
- Payments.
- Notifications.
- Mobile application.

Such features require explicit approval before implementation.

---

# 4. Architecture Rules

The project is a modular monorepo.

Required top-level structure:

```text
frontend/
backend/
database/
infrastructure/
docs/
scripts/
```

Do not rename `frontend/` and `backend/` to `apps/web` and `apps/api` unless explicitly requested.

The backend is a modular monolith.

Do not convert it into microservices.

---

# 5. Frontend Rules

Frontend uses:

- Next.js.
- React.
- TypeScript.
- Tailwind CSS.

Use feature-based organization:

```text
features/
├── auth/
├── files/
├── folders/
├── sharing/
└── storage/
```

Do not create giant components.

Prefer:

```text
feature/
├── components/
├── hooks/
├── api.ts
└── types.ts
```

Keep API communication separate from UI rendering.

Do not place backend secrets in frontend code.

---

# 6. Backend Rules

Backend uses:

- Python.
- FastAPI.
- SQLAlchemy.
- Pydantic.
- Alembic.

Business modules:

```text
auth/
files/
folders/
sharing/
storage/
```

Keep routers thin.

Business rules belong in services/modules.

Do not put all business logic in `main.py`.

Do not create giant generic files such as:

```text
utils.py
helpers.py
services.py
```

unless their responsibility is clearly defined.

---

# 7. Database Rules

Use PostgreSQL.

Use SQLAlchemy for application access.

Use Alembic for schema migrations.

Never manually modify production database structure without a corresponding migration.

Never store plaintext passwords.

Do not store binary file contents in PostgreSQL.

Store:

```text
PostgreSQL → metadata
S3 → file contents
```

Maintain foreign-key relationships and ownership constraints.

---

# 8. Storage Rules

All object-storage access must go through a storage abstraction.

Expected structure:

```text
backend/app/infrastructure/storage/
├── interface.py
├── local.py
└── s3.py
```

Business logic must depend on the abstraction rather than directly on boto3.

Never hardcode:

- AWS access keys.
- AWS secret keys.
- database passwords.
- JWT secrets.

Use environment variables or approved secret management.

---

# 9. Security Rules

Never commit:

```text
.env
.env.local
AWS credentials
private keys
database passwords
JWT secrets
```

Only commit:

```text
.env.example
```

with placeholder values.

Every protected resource must perform server-side authorization.

Never trust:

- user IDs supplied by the client,
- folder IDs supplied by the client,
- file ownership claims from the client.

Always derive the current user from authenticated credentials.

---

# 10. Sharing Rules

Share tokens must be generated using a cryptographically secure random mechanism.

Never use:

```text
file_id
user_id
timestamp
incrementing number
```

as the share token.

Every public share request must verify:

1. Token exists.
2. Token has not expired.
3. Associated file exists.
4. Associated object can be retrieved.

Expired links must not provide access.

---

# 11. Development Workflow

Work one logical step at a time.

Before changing code:

1. Inspect the current implementation.
2. Identify the exact files involved.
3. Explain the intended change internally.
4. Make the smallest correct change.
5. Run relevant tests/checks.
6. Inspect the diff.
7. Report what changed.

Do not perform unrelated cleanup during feature work.

---

# 12. No Unnecessary Rewrites

If an existing implementation works, preserve it.

Do not rewrite code merely because another architecture looks cleaner.

Before replacing working code, determine:

- What is wrong?
- Is the problem reproducible?
- Can a smaller fix solve it?
- Will the change break existing behavior?

Prefer incremental changes.

---

# 13. Dependency Rules

Do not add a dependency simply because it is convenient.

Before adding one:

1. Check whether an existing dependency already solves the problem.
2. Check whether the standard library is sufficient.
3. Consider maintenance and project complexity.
4. Add the dependency only if justified.

Record important new dependencies in documentation.

---

# 14. API Contract Rules

Frontend and backend must agree on API contracts.

Before implementing integration:

- Define endpoint.
- Define request.
- Define response.
- Define errors.
- Define authentication requirements.

Do not silently change response structures that the frontend already depends on.

If an API change is required, update both sides deliberately.

---

# 15. Error Handling Rules

Do not hide errors.

Bad:

```python
try:
    ...
except Exception:
    pass
```

Errors must either be:

- handled meaningfully, or
- logged and propagated appropriately.

Do not expose sensitive internal exceptions to users.

Return consistent API errors.

---

# 16. Testing Rules

After modifying backend logic, run the relevant tests.

At minimum, verify affected functionality.

Before declaring a feature complete:

```text
Implementation
      ↓
Test
      ↓
Integration check
      ↓
Diff review
      ↓
Done
```

Never claim a feature works without verification.

---

# 17. Commands

All commands given to teammates must be:

- copy-pasteable,
- executed from a clearly stated directory,
- appropriate for the project's actual environment.

Do not assume a command works from the repository root if it requires a subdirectory.

If a command depends on an environment variable, show the required setup.

---

# 18. Git Rules

Do not commit:

```text
.env
node_modules/
.venv/
__pycache__/
.next/
dist/
build/
local database files
temporary files
debug dumps
```

Use focused commits.

Good:

```text
feat(auth): add JWT login
feat(files): implement S3 upload
feat(sharing): add expiring links
fix(files): validate file ownership
```

Avoid:

```text
update
changes
final
final2
working
```

Never rewrite shared history unless explicitly requested.

---

# 19. Team Ownership

### Member 1

Primary ownership:

```text
backend/modules/files/
backend/modules/folders/
backend/modules/storage/
backend/infrastructure/storage/
infrastructure/aws/
```

### Member 2

Primary ownership:

```text
frontend/
```

### Member 3

Primary ownership:

```text
backend/modules/auth/
backend/modules/sharing/
backend/database/
database/
```

Ownership does not prevent collaboration.

---

# 20. Academic Evidence Rules

The application must continuously produce evidence for:

### FA1

- Frontend/UI.
- Database design.

### FA2

- Backend implementation.
- Database integration.

Do not wait until the end to collect screenshots.

Whenever a major feature becomes stable, record:

- what was implemented,
- how it was tested,
- what screenshot/evidence is useful.

---

# 21. AI Agent Behavior

The AI agent must:

- Read the relevant files before editing.
- Respect the existing architecture.
- Avoid inventing files or APIs that do not exist.
- Never claim to have run a command that it did not run.
- Never claim a test passed without actually running it.
- Never fabricate cloud credentials, URLs, IDs, or deployment results.
- Clearly distinguish implemented functionality from planned functionality.
- Ask for clarification when a decision materially changes architecture or scope.
- Prefer the smallest correct implementation.

---

# 22. One Logical Step Rule

Do not implement multiple unrelated phases in one operation.

Example:

Do not simultaneously:

```text
rewrite authentication
+
change database schema
+
redesign frontend
+
deploy AWS
```

Instead:

```text
Step 1 → database/auth foundation
Step 2 → authentication API
Step 3 → frontend authentication
Step 4 → integration
Step 5 → test
```

---

# 23. Preserve Working Behavior

Every feature must be treated as potentially dependent upon by another team member.

Before changing shared code:

- inspect usages,
- inspect API consumers,
- inspect tests,
- preserve compatibility where practical.

---

# 24. Stop Conditions

The AI agent must stop and ask before:

- changing the core architecture,
- introducing microservices,
- replacing the database,
- replacing the frontend framework,
- replacing FastAPI,
- changing authentication strategy,
- introducing major new infrastructure,
- deleting substantial existing functionality,
- adding unrelated features.

---

# 25. Definition of a Safe Change

A safe change is:

```text
Small
+
Scoped
+
Tested
+
Compatible
+
Documented when necessary
```

The objective is not maximum code.

The objective is a correct, understandable, demonstrable CloudVault system.
