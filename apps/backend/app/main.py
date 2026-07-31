from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.middleware.auth import verify_api_key
from app.routers import chat, health, knowledge_bases

app = FastAPI(
    title="Universal RAG API",
    version="1.0.0",
    description="Domain-agnostic hybrid retrieval with grounded answers and citations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path == "/api/v1/health":
        return await call_next(request)

    try:
        await verify_api_key(request.headers.get("X-API-Key") or "")
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return await call_next(request)


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(knowledge_bases.router)
if settings.enable_evaluation:
    from app.routers import evaluation

    app.include_router(evaluation.router)
