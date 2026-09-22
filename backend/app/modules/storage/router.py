from fastapi import APIRouter

router = APIRouter(
    prefix="/api/storage",
    tags=["Storage"],
)


@router.get("/health")
def storage_health() -> dict[str, str]:
    return {
        "module": "storage",
        "status": "ok",
    }
