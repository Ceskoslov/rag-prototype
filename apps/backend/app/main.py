from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.middleware.auth import verify_api_key
from app.routers import chat, evaluation, health

app = FastAPI(title="Multi-Agent RAG Backend")


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path == "/api/v1/health":
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
app.include_router(evaluation.router)
