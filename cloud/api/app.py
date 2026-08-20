"""
OMS Cloud — Main FastAPI Application
Production-ready Cloud API with Database Persistence and Edge Sync.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cloud.database.session import init_database
from cloud.routes import edge, events, cameras, analytics

app = FastAPI(
    title="OMS Sentinel Cloud API",
    description="Autonomous Surveillance Cloud Control Plane (Zero Cloud GPU Required)",
    version="9.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for worldwide frontend access (Vercel, Localhost, Mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema on startup
@app.on_event("startup")
def on_startup():
    init_database()

# Include Modular API Routers
app.include_router(edge.router)
app.include_router(events.router)
app.include_router(cameras.router)
app.include_router(analytics.router)


@app.get("/")
def root_endpoint():
    return {
        "system": "OMS Sentinel Cloud Hub",
        "version": "9.0.0",
        "status": "ONLINE",
        "docs": "/docs",
        "architecture": "Edge-Compute / Cloud-Relay"
    }
