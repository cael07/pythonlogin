from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .database import init_db
from .auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PythonLogin — Multi-App Auth Service",
    description="Reusable authentication framework with facial registration",
    version="1.0.0",
    lifespan=lifespan,
)

# Global exception handler for debugging 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {str(exc)}")
    import traceback
    traceback.print_exc()
    return {
        "detail": "Internal Server Error",
        "error": str(exc)
    }, 500

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pythonlogin-h4ev.onrender.com",
        "https://pythonlogin-h4ev.onrender.com/",
        "http://localhost:5173",
        "http://localhost:5173/",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve stored face images statically
FACE_DIR = os.path.join(os.path.dirname(__file__), "face_images")
os.makedirs(FACE_DIR, exist_ok=True)
app.mount("/face_images", StaticFiles(directory=FACE_DIR), name="face_images")

app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "service": "PythonLogin Auth API",
        "docs": "/docs",
        "health": "/auth/health",
    }
