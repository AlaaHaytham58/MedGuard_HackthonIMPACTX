import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_pipeline_search_single_medicine_name():
    response = client.post(
        "/pipeline",
        data={"medicine_name": "Brufen"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "drugs" in data
    assert len(data["drugs"]) > 0
    assert data["drugs"][0]["brand"] == "Brufen"
    assert data["status"] in ("no_record_found", "interaction_found", "unresolved")


def test_pipeline_search_medicine_names_json_list():
    response = client.post(
        "/pipeline",
        data={"medicine_names": json.dumps(["Brufen", "Marevan"])},
    )
    assert response.status_code == 200
    data = response.json()
    assert "drugs" in data
    assert len(data["drugs"]) == 2
    drug_names = [d["brand"] for d in data["drugs"]]
    assert "Brufen" in drug_names
    assert "Marevan" in drug_names


def test_pipeline_search_with_conditions():
    response = client.post(
        "/pipeline",
        data={
            "medicine_names": json.dumps(["Brufen"]),
            "conditions": json.dumps(["high_blood_pressure"]),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "conditionWarnings" in data
    warnings = data["conditionWarnings"]
    assert any(w["condition"] == "high_blood_pressure" for w in warnings)


def test_pipeline_no_input_error_message():
    response = client.post(
        "/pipeline",
        data={},
    )
    assert response.status_code == 400
    detail = response.json().get("detail", {})
    assert detail.get("code") == "NO_INPUT_PROVIDED"
    assert "Please enter a medicine name or upload an image." in detail.get("message", "")
