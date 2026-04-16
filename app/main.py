import logging

from fastapi import FastAPI

from app.routes.ai_routes import router as ai_router
from app.routes.action_routes import router as action_router
from app.routes.auth_routes import router as auth_router
from app.routes.ragam_routes import router as ragam_router
from app.routes.voice_routes import router as voice_router
from app.services import db_service, sla_service

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="VaaniSeva Multi-Module Backend", version="1.0.0")
app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(ai_router)
app.include_router(action_router)
app.include_router(ragam_router)


@app.on_event("startup")
def startup_event() -> None:
    db_service.init_db()
    sla_service.start_sla_background_monitor()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "modules": ["voice", "ai", "action"]}
