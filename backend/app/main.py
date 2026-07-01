from fastapi import FastAPI

from app.api.analyze import router as analyze_router
from app.api.auth import router as auth_router
from app.api.consent import router as consent_router
from app.api.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(consent_router)
app.include_router(analyze_router)
