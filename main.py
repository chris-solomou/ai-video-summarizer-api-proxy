from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Dict, List
from datetime import datetime
from starlette.middleware.sessions import SessionMiddleware
from models import PubSubMessage, SignedUrlResponse, SignedURLRequest, FormData
from fastapi.staticfiles import StaticFiles
from google.cloud import storage
from google.cloud import pubsub_v1
from services.gcp import StorageBucket, PubSubPublisher
from utils import generate_signed_urls, verify_email_domain, verify_jwt_token
import json
import time
import os
from dotenv import load_dotenv
from jose import jwt
from oauth import google
from jose import jwt, JWTError, ExpiredSignatureError


load_dotenv()

ALGORITHM = "HS256"
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
BUCKET_NAME = "ai-video-summarizer-dev-bucket"
TOPIC = "topic"

storage_client = storage.Client()
storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=storage_client)


publisher_client = pubsub_v1.PublisherClient()
publisher = PubSubPublisher(client=publisher_client, pubsub_topic=TOPIC)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=API_SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/auth/google/login")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await google.authorize_redirect(request, redirect_uri)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Response:
    token = request.cookies.get("token")
    payload = (
        verify_jwt_token(token=token, secret_key=API_SECRET_KEY, algorithm=ALGORITHM)
        if token
        else None
    )
    if not payload:
        response = RedirectResponse("/auth/google/login")
        response.delete_cookie("token")
        return response
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    with open("actions.json", "r") as f:
        actions = json.load(f)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "actions": actions}
    )


@app.post("/generate-signed-urls")
async def get_signed_urls(
    request: SignedURLRequest,
) -> Dict[str, List[SignedUrlResponse]]:
    file_names = [file["filename"] for file in request.files]
    signed_urls = generate_signed_urls(
        file_names=file_names, storage_bucket=storage_bucket
    )

    return {"files": signed_urls}


@app.post("/submit-form-data")
async def submit_metadata(form_data: FormData) -> None:

    # store data from the initial request here

    data = form_data.model_dump()
    video_ids = data.pop("video_ids")
    for video_id in video_ids:
        message = PubSubMessage(
            video_id=video_id, metadata=data.copy(), processing_timestamp=datetime.now()
        ).model_dump()
        publisher.publish_message(message=message)


@app.get("/auth/google/callback")
async def google_callback(request: Request) -> RedirectResponse:
    token = await google.authorize_access_token(request)
    request.session.clear()

    user_info = token["userinfo"]
    email = user_info["email"]
    if not verify_email_domain(email):
        raise ValueError("Not Allowed")  # replace with a 403 template later

    jwt_token = jwt.encode(
        {"sub": user_info["email"], "exp": int(time.time()) + 360},
        API_SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = RedirectResponse("/")
    response.set_cookie("token", jwt_token, httponly=True, samesite="lax", max_age=360)
    return response


@app.get("/check-complete")
async def check_complete(): ...
