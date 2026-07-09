import asyncio
import json
import logging
import sys
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import sarvam

from app.config import get_settings
from app.services import answer_doubts_with_retrieval, detect_car_buying_doubt

logger = logging.getLogger("autoelite.listener_agent")

CUSTOMER_IDENTITY = "customer"
CONSULTANT_IDENTITY = "consultant"
INSIGHT_TOPIC = "autoelite.insight"
DEDUP_SECONDS = 60
TRANSCRIPT_WINDOW_SECONDS = 30


class SilentListenerAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You silently transcribe customer speech for a sales consultant. "
                "Do not speak, publish audio, or generate replies."
            ),
            llm=None,
            tts=None,
        )


class TranscriptWindow:
    def __init__(self, window_seconds: int = TRANSCRIPT_WINDOW_SECONDS) -> None:
        self.window_seconds = window_seconds
        self.items: deque[tuple[float, str]] = deque()

    def append(self, text: str) -> None:
        now = time.time()
        self.items.append((now, text))
        self._trim(now)

    def text(self) -> str:
        self._trim(time.time())
        return " ".join(text for _, text in self.items)

    def _trim(self, now: float) -> None:
        while self.items and now - self.items[0][0] > self.window_seconds:
            self.items.popleft()


async def entrypoint(ctx: JobContext) -> None:
    settings = get_settings()
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)

    car_context = room_car_context(ctx.room.metadata)
    subscribe_only_to_customer_audio(ctx.room)

    transcript_window = TranscriptWindow()
    surfaced: dict[str, float] = {}
    lock = asyncio.Lock()

    session = AgentSession(
        stt=sarvam.STT(
            model="saaras:v3",
            mode="codemix",
            language="hi-IN",
            flush_signal=True,
            api_key=settings.sarvam_api_key or None,
        ),
        turn_detection="stt",
        min_endpointing_delay=0.07,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: Any) -> None:
        if not event.is_final:
            return
        utterance = event.transcript.strip()
        if not utterance:
            return
        asyncio.create_task(
            process_utterance(
                room=ctx.room,
                car_context=car_context,
                transcript_window=transcript_window,
                surfaced=surfaced,
                utterance=utterance,
                settings=settings,
                lock=lock,
            )
        )

    await session.start(
        SilentListenerAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            participant_identity=CUSTOMER_IDENTITY,
            text_enabled=False,
            audio_enabled=True,
            video_enabled=False,
            close_on_disconnect=False,
        ),
        room_output_options=RoomOutputOptions(
            audio_enabled=False,
            transcription_enabled=False,
        ),
    )


async def process_utterance(
    *,
    room: rtc.Room,
    car_context: str,
    transcript_window: TranscriptWindow,
    surfaced: dict[str, float],
    utterance: str,
    settings: Any,
    lock: asyncio.Lock,
) -> None:
    async with lock:
        transcript_window.append(utterance)
        detection = await detect_car_buying_doubt(transcript_window.text(), settings)
        if detection is None:
            return

        now = time.time()
        last_seen = surfaced.get(detection.category)
        if last_seen and now - last_seen < DEDUP_SECONDS:
            return

        try:
            answers = await answer_doubts_with_retrieval(
                car_context,
                [detection.extracted_query],
                settings,
            )
        except Exception:
            logger.exception("failed to synthesize surfaced insight")
            return

        if not answers:
            return
        card = answers[0]
        answer = (card.get("answer") or "").strip()
        if not answer or is_mode1_fallback(answer):
            logger.info("skipping empty or fallback insight for category %s", detection.category)
            return

        surfaced[detection.category] = now
        payload = {
            "type": "sales_story",
            "category": detection.category,
            "doubt": card.get("doubt") or detection.extracted_query,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await room.local_participant.publish_data(
                json.dumps(payload, ensure_ascii=False),
                reliable=True,
                destination_identities=[CONSULTANT_IDENTITY],
                topic=INSIGHT_TOPIC,
            )
        except Exception:
            logger.exception("failed to publish surfaced insight")


def room_car_context(metadata: str | None) -> str:
    if metadata:
        try:
            parsed = json.loads(metadata)
            value = str(parsed.get("car_context") or "").strip()
            if value:
                return value
        except json.JSONDecodeError:
            logger.warning("room metadata is not valid JSON")
    return "Mahindra XUV700"


def subscribe_only_to_customer_audio(room: rtc.Room) -> None:
    def subscribe_publication(
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        should_subscribe = (
            participant.identity == CUSTOMER_IDENTITY
            and publication.kind == rtc.TrackKind.KIND_AUDIO
        )
        publication.set_subscribed(should_subscribe)

    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            subscribe_publication(publication, participant)

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        for publication in participant.track_publications.values():
            subscribe_publication(publication, participant)

    @room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        subscribe_publication(publication, participant)


def is_mode1_fallback(answer: str) -> bool:
    lowered = answer.lower()
    return (
        "couldn't confirm this from live sources" in lowered
        or "couldn't synthesize a reliable answer" in lowered
    )


if __name__ == "__main__":
    settings = get_settings()
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.livekit_url or None,
            api_key=settings.livekit_api_key or None,
            api_secret=settings.livekit_api_secret or None,
            agent_name="",
        )
    )
