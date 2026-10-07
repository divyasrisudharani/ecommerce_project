from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "openapi" in response.json()
def test_required_routes_exist():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/products" in paths
    assert "/orders" in paths
    assert "/payments" in paths