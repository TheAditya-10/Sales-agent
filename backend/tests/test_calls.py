from unittest.mock import AsyncMock, MagicMock

from livekit import api as livekit_api

from app import main as main_module


class FakeLiveKitAPI:
    """Stands in for the real LiveKit control-plane client so unit tests don't need network access."""

    instances = []

    def __init__(self, url, key, secret):
        self.url = url
        self.key = key
        self.secret = secret
        self.room = MagicMock()
        self.room.create_room = AsyncMock(return_value=None)
        self.aclose = AsyncMock(return_value=None)
        FakeLiveKitAPI.instances.append(self)


def test_create_call_returns_room_and_identities(client, monkeypatch):
    FakeLiveKitAPI.instances.clear()
    monkeypatch.setattr(main_module.livekit_api, "LiveKitAPI", FakeLiveKitAPI)

    lead_response = client.post(
        "/api/leads",
        json={
            "name": "Aryan Sharma",
            "phone": "+91 98765 43210",
            "car_context": "Mahindra XUV700",
            "doubts_summary": "Comparison with Safari",
        },
    )
    lead_id = lead_response.json()["id"]

    response = client.post("/api/calls", json={"lead_id": lead_id})
    assert response.status_code == 200
    body = response.json()

    assert body["room_name"].startswith(f"autoelite-{lead_id}-")
    assert body["livekit_url"]
    assert body["consultant_token"]
    assert body["customer_token"]
    assert body["consultant_token"] != body["customer_token"]

    assert len(FakeLiveKitAPI.instances) == 1
    assert FakeLiveKitAPI.instances[0].room.create_room.await_count == 1

    settings = main_module.settings
    verifier = livekit_api.TokenVerifier(settings.livekit_api_key, settings.livekit_api_secret)

    consultant_claims = verifier.verify(body["consultant_token"])
    customer_claims = verifier.verify(body["customer_token"])

    assert consultant_claims.identity == "consultant"
    assert customer_claims.identity == "customer"
    assert consultant_claims.video.room == body["room_name"]
    assert customer_claims.video.room == body["room_name"]


def test_create_call_with_guest_negative_lead_id_uses_default_context(client, monkeypatch):
    FakeLiveKitAPI.instances.clear()
    monkeypatch.setattr(main_module.livekit_api, "LiveKitAPI", FakeLiveKitAPI)

    response = client.post("/api/calls", json={"lead_id": -1})
    assert response.status_code == 200
    body = response.json()
    assert body["room_name"].startswith("autoelite--1-")


def test_create_call_unknown_positive_lead_id_returns_404(client, monkeypatch):
    FakeLiveKitAPI.instances.clear()
    monkeypatch.setattr(main_module.livekit_api, "LiveKitAPI", FakeLiveKitAPI)

    response = client.post("/api/calls", json={"lead_id": 999999})
    assert response.status_code == 404


def test_create_call_missing_livekit_config_returns_500(client, monkeypatch):
    monkeypatch.setattr(main_module.settings, "livekit_url", "")
    response = client.post("/api/calls", json={"lead_id": -1})
    assert response.status_code == 500
