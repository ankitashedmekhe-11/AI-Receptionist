from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db.session import init_db
from routes.appointments import router as appointments_router
from routes.dashboard import router as dashboard_router
from routes.tts import router as tts_router
from routes.websocket import router as websocket_router
from routes.calls import router as calls_router
from routes.customers import router as customers_router
from routes.settings import router as settings_router
from services import stt
from services import nlu
from services import tts


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    stt.init_stt()
    nlu.init_nlu()
    yield


app = FastAPI(
    title="AI Voice Receptionist",
    description="Phase 2: appointment CRUD + WebSocket STT",
    version="0.2.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(appointments_router)
app.include_router(dashboard_router)
app.include_router(tts_router)
app.include_router(websocket_router)
app.include_router(calls_router)
app.include_router(customers_router)
app.include_router(settings_router)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
