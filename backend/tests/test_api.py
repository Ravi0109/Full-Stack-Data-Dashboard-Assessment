from __future__ import annotations


def test_health_endpoint_reports_loaded_sources(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["source_counts"]["orders"] == 2
    assert payload["source_counts"]["products"] == 3
    assert payload["source_counts"]["shipments"] == 2


def test_orders_endpoint_filters_and_paginates(client):
    response = client.get(
        "/orders?category=Electronics&page=1&page_size=1&sort_by=total_value&sort_dir=desc"
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["total"] == 1
    assert payload["data"][0]["order_id"] == "1001"
    assert payload["data"][0]["converted_total_value"] == 22.0


def test_orders_endpoint_validates_sort(client):
    response = client.get("/orders?sort_by=not_a_field")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Unsupported sort field: not_a_field"
