from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.routes import router
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Omega FundGuard — AI-Agent-Coordinated, Human-Approved, Auditable Payout Platform for Hackathons and Competitions."
)

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "api": "/api/v1",
        "settlement_mode": settings.settlement_mode,
        "stellar_testnet_enabled": settings.allow_stellar_testnet,
        "mainnet_enabled": settings.allow_stellar_mainnet
    }
