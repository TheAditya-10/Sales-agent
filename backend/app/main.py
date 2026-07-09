import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from livekit import api as livekit_api
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import Lead
from .schemas import CallCreateRequest, CallCreateResponse, ChatStreamRequest, LeadCreate, LeadRead
from .services import (
    answer_doubts_with_retrieval,
    classify_intent,
    split_doubts,
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
        status_events: asyncio.Queue[dict | None] = asyncio.Queue()

        async def on_status(data: dict) -> None:
            await status_events.put(data)
            await asyncio.sleep(0.15)

        async def run_answers() -> list[dict[str, str]]:
            try:
                return await answer_doubts_with_retrieval(
                    payload.car_context,
                    doubts,
                    settings,
                    on_status=on_status,
                )
            finally:
                await status_events.put(None)

        answer_task = asyncio.create_task(run_answers())
        while True:
            status_event = await status_events.get()
            if status_event is None:
                break
            yield sse("status", status_event)

        answers = await answer_task

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


@app.post("/api/calls", response_model=CallCreateResponse)
async def create_call(payload: CallCreateRequest, db: Session = Depends(get_db)) -> CallCreateResponse:
    if not settings.livekit_url or not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(status_code=500, detail="LiveKit is not configured")

    lead = db.get(Lead, payload.lead_id)
    if lead is None and payload.lead_id >= 0:
        raise HTTPException(status_code=404, detail="lead not found")

    car_context = lead.car_context if lead else "Mahindra XUV700"
    room_name = f"autoelite-{payload.lead_id}-{uuid.uuid4().hex[:10]}"
    room_metadata = json.dumps(
        {
            "lead_id": payload.lead_id,
            "car_context": car_context,
            "consultant_identity": "consultant",
            "customer_identity": "customer",
        },
        ensure_ascii=False,
    )

    livekit = livekit_api.LiveKitAPI(
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret,
    )
    try:
        await livekit.room.create_room(
            livekit_api.CreateRoomRequest(
                name=room_name,
                metadata=room_metadata,
                empty_timeout=20 * 60,
                max_participants=4,
            )
        )
    finally:
        await livekit.aclose()

    return CallCreateResponse(
        room_name=room_name,
        consultant_token=make_livekit_token(room_name, "consultant", room_metadata),
        customer_token=make_livekit_token(room_name, "customer", room_metadata),
        livekit_url=settings.livekit_url,
    )


def make_livekit_token(room_name: str, identity: str, metadata: str) -> str:
    return (
        livekit_api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name("Consultant" if identity == "consultant" else "Customer")
        .with_metadata(metadata)
        .with_grants(
            livekit_api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
