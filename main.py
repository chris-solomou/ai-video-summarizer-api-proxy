from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List
from datetime import datetime
from models import PubSubMessage, SignedUrlResponse, SignedURLRequest, FormData
from fastapi.staticfiles import StaticFiles
from google.cloud import storage
from google.cloud import pubsub_v1
from services.gcp import StorageBucket, PubSubPublisher
from utils import generate_signed_urls
import json

BUCKET_NAME = "ai-video-summarizer-dev-bucket"
TOPIC = "topic"

storage_client = storage.Client()
storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=storage_client)


publisher_client = pubsub_v1.PublisherClient()
publisher = PubSubPublisher(client=publisher_client, pubsub_topic=TOPIC)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Any:
    return templates.TemplateResponse(request,"index.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    with open("actions.json", "r") as f:
        actions = json.load(f)
    return templates.TemplateResponse("dashboard.html", {"request": request, "actions": actions})

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
