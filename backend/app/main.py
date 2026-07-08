import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import Lead
from .schemas import ChatStreamRequest, LeadCreate, LeadRead
from .services import (
    classify_intent,
    normalize_query,
    retrieve_web,
    split_doubts,
    synthesize_answer,
)

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoElite AI Sales Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retrieval_cache: dict[tuple[str, str], list] = {}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat/stream")
async def chat_stream(payload: ChatStreamRequest) -> StreamingResponse:
    if not payload.car_context.strip():
        raise HTTPException(status_code=400, detail="car_context is required")

    async def events() -> AsyncIterator[str]:
        yield sse("status", {"status": "classifying_intent"})
        intent = await classify_intent(payload.message, settings)

        if intent == "wants_consultant":
            yield sse(
                "request_handoff",
                {
                    "message": (
                        "I can have a dealership consultant call you. Please "
                        "confirm your name and phone number before I create the lead."
                    )
                },
            )
            yield sse("done", {"ok": True})
            return

        doubts = await split_doubts(payload.message, settings)
        answers = []
        for index, doubt in enumerate(doubts, start=1):
            normalized = normalize_query(doubt)
            cache_key = (payload.car_context.strip().lower(), normalized)

            yield sse(
                "status",
                {
                    "status": "searching_web",
                    "doubt": doubt,
                    "index": index,
                    "total": len(doubts),
                },
            )
            await asyncio.sleep(0.15)
            if cache_key in retrieval_cache:
                results = retrieval_cache[cache_key]
            else:
                try:
                    results = await retrieve_web(payload.car_context, doubt, settings)
                except Exception:
                    results = []
                retrieval_cache[cache_key] = results

            yield sse("status", {"status": "comparing_specs", "doubt": doubt})
            await asyncio.sleep(0.15)
            yield sse("status", {"status": "synthesizing", "doubt": doubt})
            answer = await synthesize_answer(payload.car_context, doubt, results, settings)
            answers.append({"doubt": doubt, "answer": answer})

        yield sse("final", {"answers": answers})
        yield sse("done", {"ok": True})

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/leads", response_model=LeadRead)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> Lead:
    lead = Lead(
        name=payload.name,
        phone=payload.phone,
        car_context=payload.car_context,
        doubts_summary=payload.doubts_summary,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/leads", response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db)) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(stmt).all())
