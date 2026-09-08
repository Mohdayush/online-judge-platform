from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CodeArena Online Judge", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
