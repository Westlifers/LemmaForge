from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent, context_packs, fragments, import_patch, relations, sources, topics, zotero
from app.config import ensure_local_directories
from app.db import init_db

app = FastAPI(title="LemmaForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fragments.router)
app.include_router(relations.router)
app.include_router(sources.router)
app.include_router(topics.router)
app.include_router(import_patch.router)
app.include_router(context_packs.router)
app.include_router(zotero.router)
app.include_router(agent.router)


@app.on_event("startup")
def on_startup() -> None:
    ensure_local_directories()
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True}
