from fastapi import APIRouter

router = APIRouter(
    prefix="/api/sharing",
    tags=["Sharing"],
)


@router.get("/health")
def sharing_health() -> dict[str, str]:
    return {
        "module": "sharing",
        "status": "ok",
    }
