from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_OCCUPATIONS = 1016
EXPECTED_RECOMMENDABLE = 544
SAMPLE_SOC = "11-1011.00"
MISSING_SOC = "99-9999.99"


def test_application_startup(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_endpoint(client: TestClient) -> None:
    payload = client.get("/api/v1/health").json()
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"
    assert payload["feature_version"] == "onet_30_3_v1"
    dumped = str(payload)
    assert "postgresql" not in dumped
    assert "password" not in dumped


def test_database_connectivity(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_occupation_listing(client: TestClient) -> None:
    response = client.get("/api/v1/occupations", params={"page": 1, "page_size": 20})
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total"] == EXPECTED_OCCUPATIONS
    assert payload["total_pages"] == 51
    assert len(payload["items"]) == 20
    first = payload["items"][0]
    assert first["onetsoc_code"] == SAMPLE_SOC
    assert first["title"] == "Chief Executives"
    assert "description" not in first


def test_occupation_listing_recommendable_filter(client: TestClient) -> None:
    response = client.get(
        "/api/v1/occupations",
        params={"page": 1, "page_size": 10, "recommendable": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == EXPECTED_RECOMMENDABLE
    assert all(item["recommendable"] is True for item in payload["items"])


def test_occupation_lookup(client: TestClient) -> None:
    response = client.get(f"/api/v1/occupations/{SAMPLE_SOC}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["onetsoc_code"] == SAMPLE_SOC
    assert payload["title"] == "Chief Executives"
    assert payload["job_zone"] == 5
    assert payload["recommendable"] is True
    assert payload["feature_version"] == "onet_30_3_v1"
    assert payload["onet_release"] == "30.3"
    assert payload["feature_count"] > 0
    assert "Determine and formulate policies" in payload["description"]


def test_missing_occupation(client: TestClient) -> None:
    response = client.get(f"/api/v1/occupations/{MISSING_SOC}")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "not_found"
    assert MISSING_SOC in payload["error"]["message"]


def test_pagination(client: TestClient) -> None:
    first = client.get("/api/v1/occupations", params={"page": 1, "page_size": 10}).json()
    second = client.get("/api/v1/occupations", params={"page": 2, "page_size": 10}).json()
    assert first["total"] == second["total"] == EXPECTED_OCCUPATIONS
    assert first["items"][0]["onetsoc_code"] != second["items"][0]["onetsoc_code"]
    first_codes = {item["onetsoc_code"] for item in first["items"]}
    second_codes = {item["onetsoc_code"] for item in second["items"]}
    assert first_codes.isdisjoint(second_codes)

    invalid = client.get("/api/v1/occupations", params={"page": 0, "page_size": 10})
    assert invalid.status_code == 422
    too_large = client.get("/api/v1/occupations", params={"page": 1, "page_size": 500})
    assert too_large.status_code == 422


def test_metadata_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/metadata/recommendation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["feature_version"] == "onet_30_3_v1"
    assert payload["onet_release"] == "30.3"
    assert payload["k"] == 10
    assert payload["config"]["k"] == 10
    assert payload["config"]["version"] == "config_v1"
    assert payload["metric"] == "weighted-block cosine (sklearn NearestNeighbors, algorithm=brute)"
    assert payload["block_weights"] == {
        "riasec": 0.25,
        "sia": 0.20,
        "essential_skills": 0.20,
        "transferable_skills": 0.15,
        "work_styles": 0.10,
        "knowledge": 0.10,
    }
    assert payload["allowed_k"] == [5, 10, 15]
    assert payload["default_job_zones"] == [3, 4, 5]
    dumped = str(payload)
    assert "DATABASE_URL" not in dumped
    assert "database_url" not in dumped
    assert "password" not in dumped
    assert "postgresql" not in dumped
