"""Development seed script.

Populates the database with safe, fake demo data so the team can
demonstrate users, nested folders, file metadata and share links without
inserting records by hand.

Safety rules:
- Refuses to run when ``APP_ENV=production``.
- Only fake development data: the demo passwords below are intentionally
  public, weak, development-only values — never seed real credentials.
- Passwords are still stored as real Argon2id hashes.
- File rows are *metadata only* (no object is uploaded to storage); the
  ``object_key`` values point at paths Member 1's storage layer would use.

Usage (from the repository root):

    python database/seeds/seed.py

Environment: reads ``DATABASE_URL`` from the environment or the app's
``.env`` file, exactly like the backend and Alembic do.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.base import utcnow  # noqa: E402
from app.database.models import File, Folder, ShareLink, User  # noqa: E402
from app.database.session import create_session  # noqa: E402
from app.modules.sharing.service import generate_share_token  # noqa: E402

# Fake, development-only credentials. Never reuse real passwords here.
DEMO_PASSWORD = "DemoPass123!"

DEMO_USERS = [
    {"name": "Alice Demo", "email": "alice@demo.cloudvault.local"},
    {"name": "Bob Demo", "email": "bob@demo.cloudvault.local"},
]


def seed() -> None:
    settings = get_settings()
    if settings.is_production:
        print("Refusing to seed demo data in production (APP_ENV=production).")
        sys.exit(1)

    db = create_session()
    try:
        if db.query(User).filter(User.email == DEMO_USERS[0]["email"]).one_or_none():
            print("Demo data already present — nothing to do.")
            return

        password_hash = hash_password(DEMO_PASSWORD)
        alice = User(name=DEMO_USERS[0]["name"], email=DEMO_USERS[0]["email"], password_hash=password_hash)
        bob = User(name=DEMO_USERS[1]["name"], email=DEMO_USERS[1]["email"], password_hash=password_hash)
        db.add_all([alice, bob])
        db.flush()

        # Nested folders for Alice: Documents/Reports
        documents = Folder(name="Documents", owner=alice)
        db.add(documents)
        db.flush()
        reports = Folder(name="Reports", owner=alice, parent_folder_id=documents.id)
        photos = Folder(name="Photos", owner=alice)
        bob_docs = Folder(name="Bob Docs", owner=bob)
        db.add_all([reports, photos, bob_docs])
        db.flush()

        # File metadata (no binary content in PostgreSQL — S3 would hold it).
        files = [
            File(
                owner=alice,
                folder=reports,
                file_name="project-report.pdf",
                object_key=f"users/{alice.id}/folders/{reports.id}/project-report.pdf",
                file_size=248_320,
                mime_type="application/pdf",
            ),
            File(
                owner=alice,
                folder=documents,
                file_name="notes.txt",
                object_key=f"users/{alice.id}/folders/{documents.id}/notes.txt",
                file_size=1_024,
                mime_type="text/plain",
            ),
            File(
                owner=alice,
                folder=photos,
                file_name="sunset.jpg",
                object_key=f"users/{alice.id}/folders/{photos.id}/sunset.jpg",
                file_size=2_411_520,
                mime_type="image/jpeg",
            ),
            File(
                owner=bob,
                folder=bob_docs,
                file_name="bob-presentation.pptx",
                object_key=f"users/{bob.id}/folders/{bob_docs.id}/bob-presentation.pptx",
                file_size=7_340_032,
                mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
        ]
        db.add_all(files)
        db.flush()

        # Share links: one long-lived valid link and one already-expired
        # link so expiry rejection can be demonstrated immediately.
        valid_share = ShareLink(
            file=files[0],
            token=generate_share_token(),
            expires_at=utcnow() + timedelta(days=7),
        )
        expired_share = ShareLink(
            file=files[2],
            token=generate_share_token(),
            expires_at=utcnow() - timedelta(hours=1),
        )
        db.add_all([valid_share, expired_share])
        db.commit()

        print("Seeded demo data:")
        print(f"  users:       {alice.email}, {bob.email}")
        print(f"  folders:     Documents -> Reports (nested), Photos, Bob Docs")
        print(f"  files:       {len(files)} metadata rows")
        print(f"  share links: 1 valid (7 days), 1 expired (for expiry demo)")
        print(f"  demo login:  any demo email with password {DEMO_PASSWORD!r}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
