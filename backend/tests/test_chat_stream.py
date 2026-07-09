from unittest.mock import AsyncMock

from app import main as main_module
from app import services

from .conftest import parse_sse_events

CAR_CONTEXT = "Mahindra XUV700 India, current-generation SUV"


def test_chat_stream_status_event_order(client, monkeypatch):
    """A valid request streams status events in the documented order, then final/done."""

    async def fake_classify_intent(message, settings):
        return "normal_query"

    async def fake_split_doubts(message, settings):
        return ["What is the on-road price?"]

    monkeypatch.setattr(main_module, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(main_module, "split_doubts", fake_split_doubts)

    async def fake_retrieve_web(car_context, doubt, settings):
        return [services.SearchResult(title="CarWale", url="https://carwale.com/x", content="XUV700 on-road price is 16.5 lakh in Delhi.")]

    async def fake_call_gemini(prompt, settings, *, expect_json):
        return "The on-road price is confirmed around 16.5 lakh (CarWale)."

    monkeypatch.setattr(services, "retrieve_web", fake_retrieve_web)
    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)
    services.retrieval_cache.clear()

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "message": "What is the on-road price?",
            "car_context": CAR_CONTEXT,
            "conversation_id": "conv-1",
        },
    ) as response:
        assert response.status_code == 200
        raw = "".join(response.iter_text())

    events = parse_sse_events(raw)
    event_names = [event["event"] for event in events]

    assert event_names[0] == "status"
    assert events[0]["data"]["status"] == "classifying_intent"

    status_sequence = [event["data"]["status"] for event in events if event["event"] == "status"]
    assert status_sequence == [
        "classifying_intent",
        "searching_web",
        "comparing_specs",
        "synthesizing",
    ]

    assert event_names[-1] == "done"
    final_event = next(event for event in events if event["event"] == "final")
    assert len(final_event["data"]["answers"]) == 1
    assert "16.5 lakh" in final_event["data"]["answers"][0]["answer"]


def test_chat_stream_multi_doubt_returns_distinct_answer_cards(client, monkeypatch):
    """A message with 2-3 questions returns multiple distinct answer cards, not one merged blob."""

    async def fake_classify_intent(message, settings):
        return "normal_query"

    doubts = [
        "What is the ADAS level?",
        "Is diesel automatic available?",
        "What is the on-road price in Mumbai?",
    ]

    async def fake_split_doubts(message, settings):
        return doubts

    monkeypatch.setattr(main_module, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(main_module, "split_doubts", fake_split_doubts)

    async def fake_retrieve_web(car_context, doubt, settings):
        return [services.SearchResult(title="Mahindra", url="https://mahindra.com/x", content=f"info about: {doubt}")]

    call_count = {"n": 0}

    async def fake_call_gemini(prompt, settings, *, expect_json):
        call_count["n"] += 1
        # Echo back which doubt this synthesis call is for, to prove distinct answers.
        for doubt in doubts:
            if doubt in prompt:
                return f"Answer specific to: {doubt}"
        return "generic answer"

    monkeypatch.setattr(services, "retrieve_web", fake_retrieve_web)
    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)
    services.retrieval_cache.clear()

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "message": "What is the ADAS level? Is diesel automatic available? What is the on-road price in Mumbai?",
            "car_context": CAR_CONTEXT,
            "conversation_id": "conv-2",
        },
    ) as response:
        raw = "".join(response.iter_text())

    events = parse_sse_events(raw)
    final_event = next(event for event in events if event["event"] == "final")
    answers = final_event["data"]["answers"]

    assert len(answers) == 3
    returned_doubts = [answer["doubt"] for answer in answers]
    assert returned_doubts == doubts
    returned_answers = [answer["answer"] for answer in answers]
    assert len(set(returned_answers)) == 3, "each doubt should get its own distinct answer, not a merged blob"
    for doubt, answer in zip(doubts, returned_answers):
        assert doubt in answer


def test_chat_stream_no_retrievable_info_returns_honest_fallback(client, monkeypatch):
    """When retrieval finds nothing, the honest fallback is returned, not a hallucinated answer."""

    async def fake_classify_intent(message, settings):
        return "normal_query"

    async def fake_split_doubts(message, settings):
        return ["Does it come with a hovercraft mode?"]

    monkeypatch.setattr(main_module, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(main_module, "split_doubts", fake_split_doubts)

    async def fake_retrieve_web(car_context, doubt, settings):
        return []

    monkeypatch.setattr(services, "retrieve_web", fake_retrieve_web)
    services.retrieval_cache.clear()

    called_gemini_for_synthesis = {"called": False}

    async def fake_call_gemini(prompt, settings, *, expect_json):
        called_gemini_for_synthesis["called"] = True
        return "It definitely has a hovercraft mode!"

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "message": "Does it come with a hovercraft mode?",
            "car_context": CAR_CONTEXT,
            "conversation_id": "conv-3",
        },
    ) as response:
        raw = "".join(response.iter_text())

    events = parse_sse_events(raw)
    final_event = next(event for event in events if event["event"] == "final")
    answer_text = final_event["data"]["answers"][0]["answer"]

    assert "couldn't confirm this from live sources" in answer_text
    assert "hovercraft" not in answer_text.lower()
    # synthesize_answer must short-circuit on empty results without calling the LLM at all
    assert called_gemini_for_synthesis["called"] is False


def test_chat_stream_requires_car_context(client):
    response = client.post(
        "/api/chat/stream",
        json={"message": "hello", "car_context": "   ", "conversation_id": "conv-4"},
    )
    assert response.status_code == 400
