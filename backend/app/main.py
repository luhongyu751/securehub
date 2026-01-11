from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import download, auth as auth_router, users as users_router, documents as docs_router, logs as logs_router
from app.routes import audit as audit_router
import asyncio
import logging
from app.utils.cleanup import cleanup_expired_files

app = FastAPI(title="SecureHub API")

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "SecureHub backend running"}


# include routers
app.include_router(download.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(docs_router.router, prefix="/api")
app.include_router(logs_router.router, prefix="/api")
app.include_router(audit_router.router, prefix="/api")


@app.on_event("startup")
async def start_cleanup_task():
    """Start a background task that periodically removes old temp PDF files."""
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    async def _cleaner():
        logging.getLogger("uvicorn").info("Starting temp-file cleaner task")
        while not stop_event.is_set():
            try:
                removed = cleanup_expired_files(older_than_seconds=300)
                if removed:
                    logging.getLogger("uvicorn").info(f"Removed {len(removed)} expired temp files")
            except Exception as e:
                logging.getLogger("uvicorn").error(f"Temp-file cleaner error: {e}")
            await asyncio.sleep(300)

    # schedule cleaner
    loop.create_task(_cleaner())


@app.on_event("shutdown")
async def stop_cleanup_task():
    logging.getLogger("uvicorn").info("Shutting down temp-file cleaner task")
