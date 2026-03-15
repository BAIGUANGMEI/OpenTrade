from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.ws import ws_hub
from app.services.decision_scheduler import decision_scheduler
from app.services.market_service import market_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await market_service.start()
    await decision_scheduler.start()
    yield
    await decision_scheduler.stop()
    await market_service.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    await ws_hub.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_hub.disconnect(channel, websocket)


app.include_router(api_router, prefix="/api")
