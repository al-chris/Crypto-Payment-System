# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import payments, users
from .database import engine, SQLModel
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    try:
        yield

    finally:
        # Shutdown: Close database connections
        if engine is not None:
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
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the Crypto Payment System API"}