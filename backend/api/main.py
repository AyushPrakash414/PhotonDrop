"""
PhotonDrop — FastAPI Backend Application

Main FastAPI app bringing together REST routes, WebSockets, and CORS setup
for the React frontend.

Run via:
    python -m backend.api.main
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.receiver_routes import router as receiver_router
from backend.api.sender_routes import router as sender_router
from backend.api.status_routes import router as status_router
from backend.api.websocket import router as ws_router
from shared.constants import LOG_DATE_FORMAT, LOG_FORMAT

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PhotonDrop API Server",
    description="Backend API for PhotonDrop React Dashboard",
    version="1.0.0",
)

# CORS Setup for React Vite Dev Server (http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(sender_router)
app.include_router(receiver_router)
app.include_router(status_router)
app.include_router(ws_router)

# Serve built frontend if it exists
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.get("/")
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "online", "system": "PhotonDrop Optical Core"}


def main():
    logger.info("Starting PhotonDrop Backend API Server on http://127.0.0.1:8000")
    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
