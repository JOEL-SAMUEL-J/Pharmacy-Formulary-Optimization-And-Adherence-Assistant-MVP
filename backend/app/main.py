from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.core.config import get_settings
from backend.core.constants import POC_DISCLAIMER
from backend.core.exceptions import BackendError
from backend.core.logging import configure_logging
from backend.db.session import dispose_engine


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version="2.3.0",
    description=POC_DISCLAIMER,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["root"])
def root():
    return {"name": settings.app_name, "docs": "/docs", "version": "2.3.0"}


@app.exception_handler(BackendError)
async def backend_error_handler(_: Request, exc: BackendError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc)}},
    )
