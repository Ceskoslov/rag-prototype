from __future__ import annotations

from fastapi import FastAPI, Request

from app.middleware.auth import verify_api_key
from app.routers import chat, health

app = FastAPI(title="Multi-Agent RAG Backend")


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path == "/api/v1/health":
        return await call_next(request)

    _ = await verify_api_key(request.headers.get("X-API-Key") or "")
    return await call_next(request)


app.include_router(health.router)
app.include_router(chat.router)
