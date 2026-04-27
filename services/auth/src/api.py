import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.db import init_db, redis_manager
from src.middleware import LoggingMiddleware
from src.routes import router
from src.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    await redis_manager.connect()
    logger.info("Redis connected ✓")
    await init_db()
    logger.info("PostgreSQL ready ✓")

    yield

    logger.info("Shutting down...")
    await redis_manager.disconnect()


app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def health():
    redis_ok = False
    try:
        await redis_manager.client.ping()
        redis_ok = True
    except Exception:
        pass

    return JSONResponse(
        content={"status": "ok" if redis_ok else "degraded", "redis": redis_ok},
        status_code=200 if redis_ok else 207,
    )
