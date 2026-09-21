"""Sharing API routes.

``POST /api/shares`` is authenticated and ownership-checked; the two
``GET`` endpoints are public and authorize purely on the share token and
its expiry.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import ShareLink, User
from app.database.session import get_db
from app.modules.sharing import service
from app.modules.sharing.schemas import (
    PublicShareResponse,
    ShareCreateRequest,
    ShareResponse,
    SharedFileInfo,
)
from app.modules.sharing.service import StorageNotConfiguredError

router = APIRouter(prefix="/shares", tags=["sharing"])


def _share_response(share: ShareLink) -> ShareResponse:
    """Serialize a share link together with safe file information."""
    return ShareResponse(
        id=share.id,
        token=share.token,
        share_url=service.build_share_url(share.token),
        expires_at=share.expires_at,
        created_at=share.created_at,
        file=SharedFileInfo(
            id=share.file.id,
            file_name=share.file.file_name,
            mime_type=share.file.mime_type,
            file_size=share.file.file_size,
        ),
    )


@router.post(
    "",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a share link for an owned file",
)
def create_share(
    payload: ShareCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareResponse:
    """Create a time-limited share link.

    The file must belong to the authenticated user (``403`` otherwise,
    ``404`` when the file does not exist). The token is generated with a
    cryptographically secure random source.
    """
    share = service.create_share(
        db,
        current_user=current_user,
        file_id=payload.file_id,
        expires_in=payload.expires_in,
    )
    return _share_response(share)


@router.get(
    "/{token}",
    response_model=PublicShareResponse,
    summary="Public share lookup by token",
)
def get_public_share(token: str, db: Session = Depends(get_db)) -> PublicShareResponse:
    """Return safe public information for a valid, unexpired share link.

    Unknown tokens return ``404``; expired tokens return ``410``. No
    authentication is required — the token itself is the credential.
    """
    share = service.get_public_share(db, token)
    return PublicShareResponse(
        file=SharedFileInfo(
            id=share.file.id,
            file_name=share.file.file_name,
            mime_type=share.file.mime_type,
            file_size=share.file.file_size,
        ),
        expires_at=share.expires_at,
        download_url=service.build_download_url(share.token),
    )


@router.get(
    "/{token}/download",
    summary="Download a file through a public share link",
    responses={
        200: {"description": "File content stream"},
        404: {"description": "Share link not found"},
        410: {"description": "Share link has expired"},
        501: {"description": "Storage integration not configured yet"},
    },
)
def download_shared_file(token: str, db: Session = Depends(get_db)) -> StreamingResponse:
    """Stream the shared file's content.

    Authorization is based on the share token and its expiry — not the
    owner's JWT. Object retrieval is delegated to the storage provider
    (Member 1's ``app.infrastructure.storage``); until that integration
    exists the endpoint validates the token and returns ``501``.
    """
    info = service.get_validated_download_info(db, token)

    try:
        provider = service.resolve_storage_provider()
    except StorageNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Share link is valid, but public download requires the storage "
                "integration (app/infrastructure/storage) which is not "
                "configured yet."
            ),
        ) from None

    # Contract with Member 1's storage provider:
    #   provider.download(object_key) -> binary stream of the object.
    stream = provider.download(info.object_key)
    return StreamingResponse(
        stream,
        media_type=info.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{info.file_name}"',
            "Content-Length": str(info.file_size),
        },
    )
