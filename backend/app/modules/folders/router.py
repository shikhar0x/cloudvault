from fastapi import APIRouter

router = APIRouter(
    prefix="/api/folders",
    tags=["Folders"],
)


@router.get("/health")
def folders_health() -> dict[str, str]:
    return {
        "module": "folders",
        "status": "ok",
    }
