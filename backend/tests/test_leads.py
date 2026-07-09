def test_create_lead_saves_all_fields(client):
    payload = {
        "name": "Aryan Sharma",
        "phone": "+91 98765 43210",
        "car_context": "Mahindra XUV700",
        "doubts_summary": "Comparison with Safari",
    }
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["phone"] == payload["phone"]
    assert body["car_context"] == payload["car_context"]
    assert body["doubts_summary"] == payload["doubts_summary"]
    assert body["status"] == "NEW"
    assert "id" in body
    assert "created_at" in body


def test_create_lead_missing_name_rejected_with_422_not_500(client):
    payload = {
        "phone": "+91 98765 43210",
        "car_context": "Mahindra XUV700",
        "doubts_summary": "Comparison with Safari",
    }
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 422
    assert response.status_code != 500


def test_create_lead_missing_phone_rejected_with_422_not_500(client):
    payload = {
        "name": "Aryan Sharma",
        "car_context": "Mahindra XUV700",
        "doubts_summary": "Comparison with Safari",
    }
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 422
    assert response.status_code != 500


def test_create_lead_empty_name_rejected(client):
    payload = {
        "name": "",
        "phone": "+91 98765 43210",
        "car_context": "Mahindra XUV700",
        "doubts_summary": "Comparison with Safari",
    }
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 422


def test_list_leads_returns_newest_first(client):
    for name in ["First Lead", "Second Lead", "Third Lead"]:
        response = client.post(
            "/api/leads",
            json={
                "name": name,
                "phone": "+91 90000 00000",
                "car_context": "Mahindra XUV700",
                "doubts_summary": "some doubt",
            },
        )
        assert response.status_code == 200

    response = client.get("/api/leads")
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) == 3
    names_in_order = [lead["name"] for lead in leads]
    assert names_in_order == ["Third Lead", "Second Lead", "First Lead"]

    created_ats = [lead["created_at"] for lead in leads]
    assert created_ats == sorted(created_ats, reverse=True)
