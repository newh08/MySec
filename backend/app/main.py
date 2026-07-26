from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="MySecretary API", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
