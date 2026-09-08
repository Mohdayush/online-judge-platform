from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CodeArena Online Judge", version="1.0.0", description="Asynchronous online judge with isolated execution workers.")

origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready"}


web_dir = Path(__file__).resolve().parent.parent / "web"
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
