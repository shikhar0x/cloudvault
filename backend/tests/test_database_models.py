"""Database tests: constraints, relationships, cascades and timestamps.

These run against the real PostgreSQL test database (see conftest.py),
exercising the exact semantics the application relies on.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.database.base import utcnow
from app.database.models import File, Folder, ShareLink, User

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class TestUserModel:
    def test_create_user_with_defaults(self, db, make_user):
        user = make_user(email="model-user@example.com")
        assert user.id is not None
        assert user.created_at is not None
        assert user.created_at.tzinfo is not None, "timestamp must be timezone-aware"

    def test_email_unique_constraint(self, db, make_user):
        make_user(email="dup@example.com")
        with pytest.raises(IntegrityError):
            db.add(User(name="Second", email="dup@example.com", password_hash="x"))
            db.commit()
        db.rollback()

    def test_email_lowercase_check_constraint(self, db, make_user):
        with pytest.raises(IntegrityError):
            db.add(User(name="Upper", email="UPPER@Example.com", password_hash="x"))
            db.commit()
        db.rollback()

    def test_password_never_stored_plaintext(self, db, make_user):
        user = make_user(email="hash-check@example.com", password="PlainSecret1!")
        assert user.password_hash != "PlainSecret1!"
        assert verify_password("PlainSecret1!", user.password_hash)

    def test_user_files_and_folders_relationships(self, db, make_user):
        user = make_user(email="rels@example.com")
        folder = Folder(name="Docs", owner=user)
        db.add(folder)
        db.flush()
        db.add(File(file_name="a.txt", object_key="k", file_size=1, mime_type="text/plain",
                    owner=user, folder=folder))
        db.commit()
        assert [f.name for f in user.folders] == ["Docs"]
        assert [f.file_name for f in user.files] == ["a.txt"]


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------

class TestFolderModel:
    def test_nested_folders(self, db, make_user):
        user = make_user(email="nested@example.com")
        root = Folder(name="root", owner=user)
        db.add(root)
        db.flush()
        # Assign parents through the relationship (works across unflushed rows).
        child = Folder(name="child", owner=user, parent=root)
        grandchild = Folder(name="grandchild", owner=user, parent=child)
        db.add_all([child, grandchild])
        db.commit()

        assert child.parent.name == "root"
        assert [c.name for c in root.children] == ["child"]
        assert grandchild.parent.name == "child"
        assert [c.name for c in child.children] == ["grandchild"]

    def test_folder_requires_owner(self, db, make_user):
        with pytest.raises(IntegrityError):
            db.add(Folder(name="orphan"))
            db.commit()
        db.rollback()

    def test_cross_user_parent_rejected_by_database(self, db, make_user):
        """The composite FK must stop a folder pointing at another user's folder."""
        alice = make_user(email="alice@example.com")
        bob = make_user(email="bob@example.com")
        alice_root = Folder(name="alice-root", owner=alice)
        db.add(alice_root)
        db.commit()

        with pytest.raises(IntegrityError):
            db.add(Folder(name="bob-child", owner=bob, parent_folder_id=alice_root.id))
            db.commit()
        db.rollback()

    def test_self_parent_rejected(self, db, make_user):
        user = make_user(email="selfparent@example.com")
        folder = Folder(name="loop", owner=user)
        db.add(folder)
        db.flush()
        folder.parent_folder_id = folder.id
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_folder_files_relationship(self, db, make_user):
        user = make_user(email="folder-files@example.com")
        folder = Folder(name="F", owner=user)
        db.add(folder)
        db.flush()
        db.add(File(file_name="f.txt", object_key="k", file_size=5, mime_type="text/plain",
                    owner=user, folder=folder))
        db.commit()
        assert [f.file_name for f in folder.files] == ["f.txt"]
        assert folder.files[0].folder.name == "F"


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

class TestFileModel:
    def test_file_requires_user(self, db):
        with pytest.raises(IntegrityError):
            db.add(File(file_name="x", object_key="k", file_size=1, mime_type="text/plain"))
            db.commit()
        db.rollback()

    def test_file_requires_valid_user_fk(self, db):
        import uuid as _uuid

        with pytest.raises(IntegrityError):
            db.add(File(user_id=_uuid.uuid4(), file_name="x", object_key="k",
                        file_size=1, mime_type="text/plain"))
            db.commit()
        db.rollback()

    def test_negative_file_size_rejected(self, db, make_user):
        user = make_user(email="size@example.com")
        with pytest.raises(IntegrityError):
            db.add(File(file_name="x", object_key="k", file_size=-1,
                        mime_type="text/plain", owner=user))
            db.commit()
        db.rollback()

    def test_file_can_live_at_root(self, db, make_user):
        """folder_id is nullable: root-level files are allowed."""
        user = make_user(email="rootfile@example.com")
        file = File(file_name="root.txt", object_key="k", file_size=1,
                    mime_type="text/plain", owner=user, folder=None)
        db.add(file)
        db.commit()
        assert file.folder_id is None


# ---------------------------------------------------------------------------
# Share links
# ---------------------------------------------------------------------------

class TestShareLinkModel:
    def test_share_requires_existing_file(self, db):
        import uuid as _uuid

        with pytest.raises(IntegrityError):
            db.add(ShareLink(file_id=_uuid.uuid4(), token="t", expires_at=utcnow()))
            db.commit()
        db.rollback()

    def test_token_unique_constraint(self, db, make_user):
        user = make_user(email="token-unique@example.com")
        file = File(file_name="x", object_key="k", file_size=1,
                    mime_type="text/plain", owner=user)
        db.add(file)
        db.flush()
        db.add(ShareLink(file_id=file.id, token="dup-token", expires_at=utcnow()))
        db.commit()
        with pytest.raises(IntegrityError):
            db.add(ShareLink(file_id=file.id, token="dup-token", expires_at=utcnow()))
            db.commit()
        db.rollback()

    def test_is_expired_uses_timezone_aware_comparison(self, db, make_user):
        user = make_user(email="expiry@example.com")
        file = File(file_name="x", object_key="k", file_size=1,
                    mime_type="text/plain", owner=user)
        db.add(file)
        db.flush()

        expired = ShareLink(file_id=file.id, token="expired-t", expires_at=utcnow() - timedelta(minutes=1))
        valid = ShareLink(file_id=file.id, token="valid-t", expires_at=utcnow() + timedelta(days=1))
        db.add_all([expired, valid])
        db.commit()

        assert expired.is_expired is True
        assert valid.is_expired is False


# ---------------------------------------------------------------------------
# Deletion behavior (cascades)
# ---------------------------------------------------------------------------

class TestDeletionBehavior:
    def _seed_tree(self, db, make_user):
        user = make_user(email="cascade@example.com")
        root = Folder(name="root", owner=user)
        db.add(root)
        db.flush()
        sub = Folder(name="sub", owner=user, parent_folder_id=root.id)
        db.add(sub)
        db.flush()
        file = File(file_name="in-sub.txt", object_key="k", file_size=10,
                    mime_type="text/plain", owner=user, folder=sub)
        db.add(file)
        db.flush()
        db.add(ShareLink(file_id=file.id, token="cascade-token",
                         expires_at=utcnow() + timedelta(days=1)))
        db.commit()
        return user, root, sub, file

    def test_deleting_file_removes_its_share_links(self, db, make_user):
        user, root, sub, file = self._seed_tree(db, make_user)
        db.delete(file)
        db.commit()
        assert db.query(ShareLink).count() == 0
        # ...but the folders remain
        assert db.query(Folder).count() == 2

    def test_deleting_folder_cascades_to_subfolders_files_and_shares(self, db, make_user):
        user, root, sub, file = self._seed_tree(db, make_user)
        db.delete(root)
        db.commit()
        assert db.query(Folder).count() == 0
        assert db.query(File).count() == 0
        assert db.query(ShareLink).count() == 0

    def test_deleting_user_cascades_to_everything(self, db, make_user):
        user, root, sub, file = self._seed_tree(db, make_user)
        db.delete(user)
        db.commit()
        assert db.query(User).count() == 0
        assert db.query(Folder).count() == 0
        assert db.query(File).count() == 0
        assert db.query(ShareLink).count() == 0

    def test_timestamps_persisted(self, db, make_user):
        user, root, sub, file = self._seed_tree(db, make_user)
        stored = db.query(ShareLink).one()
        assert stored.created_at is not None
        assert stored.created_at.tzinfo is not None
