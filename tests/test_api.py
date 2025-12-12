from fastapi.testclient import TestClient
from main import app
from utils import create_jwt
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ALGORITHM = "HS256"

client = TestClient(app)


def test_index_no_token_redirects():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # redirect to login
    assert response.headers["location"] == "/auth/google/login"


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


@pytest.mark.parametrize("payload", [{}])
def test_invalid_signed_urls(payload):
    response = client.post("/generate-signed-urls", json=payload)
    assert response.status_code == 422 # failed to parse


def test_get_root_authenticated():
    valid_token = create_jwt(
        email="test@productmadness.com", secret_key=API_SECRET_KEY, algorithm=ALGORITHM
    )
    response = client.get("/", cookies={"token": valid_token})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_expired_token_redirects():
    expired_token = valid_token = create_jwt(
        email="test@productmadness.com",
        secret_key=API_SECRET_KEY,
        algorithm=ALGORITHM,
        expires_in_minutes=-10,
    )
    response = client.get("/dashboard", cookies={"token": expired_token})
    assert response.status_code == 200 or response.status_code == 307


def test_index_invalid_token_redirects():
    response = client.get("/", cookies={"token": "invalid"}, follow_redirects=False)
    assert response.status_code == 307


def test_index_expired_token_redirects():
    expired_token = create_jwt(
        email="test@productmadness.com",
        secret_key=API_SECRET_KEY,
        algorithm=ALGORITHM,
        expires_in_minutes=-10,  # expired
    )

    response = client.get("/", cookies={"token": expired_token}, follow_redirects=False)
    assert response.status_code == 307


def test_index_valid_token_renders():
    valid_token = create_jwt(
        email="test@productmadness.com", secret_key=API_SECRET_KEY, algorithm=ALGORITHM
    )
    response = client.get("/", cookies={"token": valid_token})
    assert response.status_code == 200
    assert "AI Video Summary Generator" in response.text
