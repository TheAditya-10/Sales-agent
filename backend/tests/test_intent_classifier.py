import pytest

from app import services
from app.config import Settings


@pytest.fixture()
def settings():
    return Settings(gemini_api_key="dummy-key-for-test")


HANDOFF_PHRASES = [
    "I want to talk to a consultant",
    "Can someone call me back please",
    "mujhe consultant se baat karni hai",
    "Book a test drive for me",
    "Please give me your dealer's phone number",
]

NORMAL_PHRASES = [
    "What is the ground clearance of the XUV700?",
    "Kitna mileage milta hai diesel automatic mein?",
    "Compare ADAS features with Safari",
]


@pytest.mark.parametrize("message", HANDOFF_PHRASES)
async def test_handoff_phrases_classified_as_wants_consultant(message, settings, monkeypatch):
    async def fail_if_called(prompt, settings, *, expect_json):
        raise AssertionError("Gemini should not be called when the regex already detects handoff intent")

    monkeypatch.setattr(services, "call_gemini", fail_if_called)

    intent = await services.classify_intent(message, settings)
    assert intent == "wants_consultant"


@pytest.mark.parametrize("message", NORMAL_PHRASES)
async def test_normal_phrases_do_not_falsely_trigger_handoff(message, settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return "normal_query"

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    intent = await services.classify_intent(message, settings)
    assert intent == "normal_query"


async def test_chat_stream_endpoint_skips_retrieval_on_handoff(client, monkeypatch):
    """When intent is wants_consultant, the endpoint must not call split_doubts/retrieval at all."""
    from app import main as main_module

    async def fake_classify_intent(message, settings):
        return "wants_consultant"

    def fail_split_doubts(*args, **kwargs):
        raise AssertionError("split_doubts must not be called on handoff intent")

    monkeypatch.setattr(main_module, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(main_module, "split_doubts", fail_split_doubts)

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "message": "mujhe consultant se baat karni hai",
            "car_context": "Mahindra XUV700",
            "conversation_id": "conv-handoff",
        },
    ) as response:
        raw = "".join(response.iter_text())

    from .conftest import parse_sse_events

    events = parse_sse_events(raw)
    event_names = [event["event"] for event in events]
    assert "request_handoff" in event_names
    assert "final" not in event_names
    assert event_names[-1] == "done"
