from fastapi import Body, FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional, List, Union
import uuid
from datetime import datetime
from models import PubSubMessage, SignedUrlResponse, SignedURLRequest, FormData
from fastapi.staticfiles import StaticFiles
from google.cloud import storage
from sources.gcp import StorageBucket, PubSubPublisher


def generate_video_id(file: Union[UploadFile, str]) -> str:
    if isinstance(file, UploadFile):
        file_name = file.filename
    elif isinstance(file, str):
        file_name = file
    else:
        raise TypeError(f"File of type {type(file)} is not supported!")
    ext = file_name.split(".")[-1]
    return str(uuid.uuid4()) + "." + ext


BUCKET_NAME = "ai-video-summarizer-dev-bucket"
client = storage.Client()
storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=client)

publisher = PubSubPublisher(pubsub_topic="topic")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request) -> Any:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate-signed-urls")
async def get_signed_urls(request: SignedURLRequest) -> Dict[str, List[SignedUrlResponse]]:
    file_names = [file["filename"] for file in request.files]

    signed_urls = []
    try:
        for file in file_names:
            video_id = generate_video_id(file=file)
            signed_url = storage_bucket.generate_dummy_signed_url(blob_name=video_id)
            signed_urls.append({"video_id": video_id, "signed_url": signed_url})
    except Exception as e:
        print(f"The folloing exception has occurred {e}!")

    return {"files": signed_urls}


@app.post("/submit-form-data")
async def submit_metadata(form_data: FormData) -> None:
    data = form_data.model_dump()
    video_ids = data.pop("video_ids")
    for video_id in video_ids:
        message = PubSubMessage(
            video_id=video_id, metadata=data.copy(), processing_timestamp=datetime.now()
        ).model_dump()
        publisher.publish_message(message=message)
