from fastapi import Body, FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional, List, Union
import uuid
from datetime import datetime
from models import PubSubMessage, SignedUrlResponse, SignedURLRequest, Metadata
from fastapi.staticfiles import StaticFiles
from google.cloud import storage
from sources.gcp import StorageBucket


def generate_video_id(file: Union[UploadFile, str]) -> str:
    if isinstance(file, UploadFile):
        file_name = file.filename
    elif isinstance(file, str):
        file_name = file
    else:
        raise TypeError(f"File of type {file} is not supported!")
    ext = file_name.split(".")[-1]
    return str(uuid.uuid4()) + "." + ext


BUCKET_NAME = "ai-video-summarizer-dev-bucket"
client = storage.Client()
storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=client)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    # await print(request.json())
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate-signed-urls")
async def get_signed_urls(request: SignedURLRequest):
    file_names = [file["filename"] for file in request.files]

    signed_urls = []
    try:
        for file in file_names:
            video_id = generate_video_id(file=file)
            signed_url = storage_bucket.generate_dummy_signed_url(
                blob_name=video_id
            )
            signed_urls.append({"video_id": video_id, "signed_url": signed_url})
    except Exception as e:
        print(f"The folloing exception has occurred {e}!")

    print(signed_urls)
    return {"files": signed_urls}


@app.post("send-to-pubsub")
def send_pubsub_message(message: Metadata): ...


@app.post("/submit-metadata")
async def submit_metadata(request: Request):
    data = await request.json()  # or await request.json() if JSON
    print(data)
    return {"data": dict(data)}
