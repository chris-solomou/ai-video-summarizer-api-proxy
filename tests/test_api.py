from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize(
    "payload",  
    [
        {
            "files": [
                {"filename": "video.mp4", "content_type": "video/mp4"},
                {"filename": "archive.tar.gz", "content_type": "application/gzip"},
            ]
        }
    ],
)
def test_valid_signed_urls(payload):
    response = client.post("/generate-signed-urls", json=payload)
    assert response.status_code == 200
    assert "files" in response.json()
    assert isinstance(response.json()["files"], list)


@pytest.mark.parametrize(
    "payload", [{}]
)
def test_invalid_signed_urls(payload):
    response = client.post("/generate-signed-urls", json=payload)
    assert response.status_code == 422
