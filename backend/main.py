"""FastAPI application entry point for ShopAgent AI."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, get_session_local
from backend.catalog import seed_catalog
from backend.api_routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager: initializes DB and seeds products."""
    init_db()
    logger.info("Database initialized successfully.")
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        added = seed_catalog(db)
        logger.info(f"Startup catalog check complete (new items: {added}).")
    except Exception as e:
        logger.error(f"Error during startup catalog seeding: {e}")
    finally:
        db.close()
    yield
    logger.info("ShopAgent AI backend shutting down.")


app = FastAPI(
    title="ShopAgent AI",
    description="Autonomous AI Buyer Agent for Razorpay Merchants — Track 01: Agentic Commerce",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    """Serve the VoltStore demo storefront or service info."""
    store_file = os.path.join(static_dir, "store.html")
    if os.path.exists(store_file):
        return FileResponse(store_file)
    return {
        "service": "ShopAgent AI",
        "tagline": "Autonomous AI Buyer Agent for Razorpay Merchants",
        "track": "Track 01: AI Growth & Agentic Commerce",
        "status": "running",
        "endpoints": {
            "api_docs": "/docs",
            "health": "/api/health",
            "products": "/api/products",
            "chat": "/api/chat",
            "dashboard_stats": "/api/stats"
        }
    }


@app.get("/store")
def store():
    """Direct route for VoltStore storefront."""
    store_file = os.path.join(static_dir, "store.html")
    if os.path.exists(store_file):
        return FileResponse(store_file)
    return {"error": "Storefront template not found."}


@app.get("/api/health")
def health():
    """Healthcheck endpoint."""
    return {
        "service": "ShopAgent AI",
        "status": "healthy",
        "track": "Track 01: AI Growth & Agentic Commerce",
        "model": "gemini-3.8-flash"
    }
