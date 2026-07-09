import json

import pytest

from app import services
from app.config import Settings


@pytest.fixture()
def settings():
    return Settings(gemini_api_key="dummy-key-for-test")


async def test_detect_car_buying_doubt_returns_category_for_real_doubt(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return json.dumps({"category": "Price / EMI", "extracted_query": "What is the EMI for AX7 Luxury?"})

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt(
        "yeh gaadi ka price kitna hai aur EMI kitni banegi har mahine", settings
    )

    assert detection is not None
    assert detection.category == "price_emi"
    assert detection.extracted_query == "What is the EMI for AX7 Luxury?"


async def test_detect_car_buying_doubt_returns_none_for_small_talk(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return "null"

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt("haan theek hai, aap kaise ho", settings)
    assert detection is None


async def test_detect_car_buying_doubt_returns_none_for_empty_transcript(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return ""

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt("", settings)
    assert detection is None


async def test_detect_car_buying_doubt_returns_none_for_malformed_json(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return "not valid json at all"

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt("some transcript", settings)
    assert detection is None


async def test_detect_car_buying_doubt_returns_none_when_category_or_query_missing(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return json.dumps({"category": "", "extracted_query": "something"})

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt("some transcript", settings)
    assert detection is None


async def test_detect_car_buying_doubt_normalizes_category_to_snake_case(settings, monkeypatch):
    async def fake_call_gemini(prompt, settings, *, expect_json):
        return json.dumps({"category": "Resale Value!!", "extracted_query": "How is resale value?"})

    monkeypatch.setattr(services, "call_gemini", fake_call_gemini)

    detection = await services.detect_car_buying_doubt("resale value ka kya scene hai", settings)
    assert detection is not None
    assert detection.category == "resale_value"
