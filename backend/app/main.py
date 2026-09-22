from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.files.router import router as files_router
from app.modules.folders.router import router as folders_router
from app.modules.sharing.router import router as sharing_router
from app.modules.storage.router import router as storage_router

settings = get_settings()

app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="Backend API for the CloudVault cloud file storage and sharing platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cloudvault-api",
    }


app.include_router(files_router)
app.include_router(folders_router)
app.include_router(storage_router)
app.include_router(sharing_router)
