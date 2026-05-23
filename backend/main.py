from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from .database import init_db
from .auth.router import router as auth_router
from .ride.router import router as ride_router
from .ocr.router import router as ocr_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
    import traceback
    err_trace = traceback.format_exc()
    print(f"CRITICAL ERROR:\n{err_trace}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "trace": err_trace
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pythonlogin-h4ev.onrender.com",
        "https://pythonlogin-h4ev.onrender.com/",
        "https://pythonlogin-driver.onrender.com",
        "https://pythonlogin-driver.onrender.com/",
        "https://pythonlogin-passenger.onrender.com",
        "https://pythonlogin-passenger.onrender.com/",
        "http://localhost:5173",
        "http://localhost:5173/",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve stored face images statically with CORS support
FACE_DIR = os.path.join(os.path.dirname(__file__), "face_images")
os.makedirs(FACE_DIR, exist_ok=True)

DRIVER_DIR = os.path.join(os.path.dirname(__file__), "driver_docs")
os.makedirs(DRIVER_DIR, exist_ok=True)

class CORSStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send):
        # We need headers here to get origin
        headers = dict(scope.get("headers", []))
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                # Find headers
                msg_headers = dict(message.get("headers", []))
                origin = headers.get(b"origin", b"*").decode()
                msg_headers[b"access-control-allow-origin"] = origin.encode()
                msg_headers[b"access-control-allow-credentials"] = b"true"
                message["headers"] = list(msg_headers.items())
            await send(message)
        await super().__call__(scope, receive, send_with_cors)

app.mount("/face_images", CORSStaticFiles(directory=FACE_DIR), name="face_images")
app.mount("/driver_docs", CORSStaticFiles(directory=DRIVER_DIR), name="driver_docs")

app.include_router(auth_router)
app.include_router(ride_router)
app.include_router(ocr_router)



@app.get("/")
async def root():
    return {
        "service": "PythonLogin Auth API",
        "docs": "/docs",
        "health": "/auth/health",
    }






