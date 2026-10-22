import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.database import engine
from app.routers import heroes, missions, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)   # create missing tables (dev convenience; Alembic is the real path)
    yield


app = FastAPI(
    title="Heroes API",
    version="1.0.0",
    openapi_tags=[
        {"name": "heroes", "description": "Create, read, update and delete heroes."},
        {"name": "teams", "description": "Teams and the heroes that belong to them."},
        {"name": "missions", "description": "Missions that heroes can be assigned to."},
    ],
    lifespan=lifespan,
)

# Browser pages on other origins (e.g. Live Server) may call the API.
# Read from an env var in deployment: CORS_ORIGINS="https://ui.example.com,https://other.example.com"
origins = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API: /api/v1/heroes, /api/v1/teams, /api/v1/missions
app.include_router(heroes.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(missions.router, prefix="/api/v1")
