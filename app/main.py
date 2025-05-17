# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import payments, users
from .database import engine
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    try:
        yield

    finally:
        # Shutdown: Close database connections
        if engine:
            await engine.dispose()
            print("Database connections closed.")
            

app = FastAPI(
    title="Crypto Payment System",
    description="API for processing and managing cryptocurrency payments. Handles transaction processing, wallet management, and payment status tracking.",
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "email": "chrisdev0000@gmail.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Initialize Routers
app.include_router(users.router)
app.include_router(payments.router)

# CORS Middleware (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    strategy="fixed-window",
    storage_uri="redis://redis:6379/0"
)

@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"message": "Welcome to the Crypto Payment System API"})