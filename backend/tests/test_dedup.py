import time
from unittest.mock import AsyncMock, MagicMock

import agent.listener_agent as listener_agent
from app.services import DoubtDetection


async def test_same_doubt_category_deduped_within_60_seconds_then_fires_again_after(monkeypatch):
    detection = DoubtDetection(category="price_emi", extracted_query="What's the EMI for AX7 Luxury?")

    async def fake_detect(text, settings):
        return detection

    async def fake_answer(car_context, doubts, settings, **kwargs):
        return [{"doubt": doubts[0], "answer": "The AX7 Luxury EMI starts near 32k/month (CarWale)."}]

    monkeypatch.setattr(listener_agent, "detect_car_buying_doubt", fake_detect)
    monkeypatch.setattr(listener_agent, "answer_doubts_with_retrieval", fake_answer)

    room = MagicMock()
    room.local_participant.publish_data = AsyncMock(return_value=None)

    surfaced: dict[str, float] = {}
    transcript_window = listener_agent.TranscriptWindow()
    lock = listener_agent.asyncio.Lock()

    await listener_agent.process_utterance(
        room=room,
        car_context="Mahindra XUV700",
        transcript_window=transcript_window,
        surfaced=surfaced,
        utterance="EMI kitni hogi AX7 Luxury ke liye",
        settings=None,
        lock=lock,
    )

    assert room.local_participant.publish_data.await_count == 1
    assert "price_emi" in surfaced

    # Rapid-fire the same doubt again immediately (well within the 60s dedup window).
    await listener_agent.process_utterance(
        room=room,
        car_context="Mahindra XUV700",
        transcript_window=transcript_window,
        surfaced=surfaced,
        utterance="haan EMI kitni hogi bataiye phir se",
        settings=None,
        lock=lock,
    )

    assert room.local_participant.publish_data.await_count == 1, "second doubt within 60s must be suppressed"

    # Simulate the 60s dedup window having passed.
    surfaced["price_emi"] = time.time() - 61

    await listener_agent.process_utterance(
        room=room,
        car_context="Mahindra XUV700",
        transcript_window=transcript_window,
        surfaced=surfaced,
        utterance="EMI ke baare mein phir se pooch raha hoon",
        settings=None,
        lock=lock,
    )

    assert room.local_participant.publish_data.await_count == 2, "same category must fire again once the window has passed"


async def test_no_doubt_detected_does_not_publish(monkeypatch):
    async def fake_detect(text, settings):
        return None

    publish_mock = AsyncMock(return_value=None)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("answer_doubts_with_retrieval must not be called when no doubt is detected")

    monkeypatch.setattr(listener_agent, "detect_car_buying_doubt", fake_detect)
    monkeypatch.setattr(listener_agent, "answer_doubts_with_retrieval", fail_if_called)

    room = MagicMock()
    room.local_participant.publish_data = publish_mock

    await listener_agent.process_utterance(
        room=room,
        car_context="Mahindra XUV700",
        transcript_window=listener_agent.TranscriptWindow(),
        surfaced={},
        utterance="haan theek hai, sab badhiya hai",
        settings=None,
        lock=listener_agent.asyncio.Lock(),
    )

    assert publish_mock.await_count == 0


async def test_fallback_answer_is_not_surfaced_as_insight(monkeypatch):
    """If the shared retrieval pipeline falls back to the honest 'couldn't confirm' text,
    the listener agent must not push it as a story card."""
    detection = DoubtDetection(category="mileage", extracted_query="What's the real-world mileage?")

    async def fake_detect(text, settings):
        return detection

    async def fake_answer(car_context, doubts, settings, **kwargs):
        return [
            {
                "doubt": doubts[0],
                "answer": (
                    "I couldn't confirm this from live sources right now. For this demo, "
                    "I won't invent specs or prices. Please try again in a moment or ask "
                    "for a consultant callback."
                ),
            }
        ]

    monkeypatch.setattr(listener_agent, "detect_car_buying_doubt", fake_detect)
    monkeypatch.setattr(listener_agent, "answer_doubts_with_retrieval", fake_answer)

    room = MagicMock()
    room.local_participant.publish_data = AsyncMock(return_value=None)

    surfaced: dict[str, float] = {}
    await listener_agent.process_utterance(
        room=room,
        car_context="Mahindra XUV700",
        transcript_window=listener_agent.TranscriptWindow(),
        surfaced=surfaced,
        utterance="real world mileage kitni milegi",
        settings=None,
        lock=listener_agent.asyncio.Lock(),
    )

    assert room.local_participant.publish_data.await_count == 0
    assert "mileage" not in surfaced
