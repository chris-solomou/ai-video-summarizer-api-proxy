from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from models import PubSubMessage
from fastapi.staticfiles import StaticFiles
import asyncio
from google.cloud import storage

"""
curl -X POST "  /params" \
     -H "Content-Type: multipart/form-data" \
     -F "user_id=123" \
     -F "task=process" \
     -F "params={}" \
     -F "file=@/Users/chris.solomou/Downloads/Screenshot 2025-11-11 at 11.55.08.png"
"""

BUCKET_PATH = "gs://ai-video-summarizer-dev-bucket"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


async def save_file(file: UploadFile) -> None:
    data = await file.read()
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(data)


def save_json(data: Dict[str, Any]) -> None:
    with open(f"submissions.json", "a") as f:
        f.write(json.dumps(data, default=str))
        f.write("\n")


def upload_to_bucket(bucket_name: str, source_file_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    pass

def generate_blob_name(file_name:str) -> str:...


def generate_upload_signed_url(bucket_name: str, blob_name: str) -> str:
    client = storage.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        # content_type="application/octet-stream",
    )
    return url


def send_to_pub_sub(data: Dict[str, Any]) -> PubSubMessage:
    return PubSubMessage(**data)

    



@app.api_route("/", methods=["GET", "POST"])
async def read_root(
    request: Request,
    # user_id: Optional[int] = Form(None), see what we get when they authenticate
    summaryType: Optional[str] = Form(None),
    audienceContext: Optional[str] = Form(None),
    uploadFiles: Optional[List[UploadFile]] = File(None),
    customPrompt: Optional[str] = Form(None),
    uploadFolder: Optional[List[UploadFile]] = File(None),
    outputFormat: Optional[str] = Form(None),
    includeScreenshots: Optional[bool] = Form(False),
    detailLevel: int = Form(1),
):

    if request.method == "GET":
        return templates.TemplateResponse("index.html", {"request": request})

    try:
        # print(await request.json())  # Removed because form-data is not JSON
        # If you want to see everything from the request, use request.form() and request.files()
        form = await request.form()
        print("Received form data:", dict(form))
        print(
            "Received files:",
            {
                "uploadFiles": (
                    [file.filename for file in uploadFiles] if uploadFiles else None
                ),
                "uploadFolder": (
                    [file.filename for file in uploadFolder] if uploadFolder else None
                ),
            },
        )
        if uploadFiles:
            tasks = [save_file(file) for file in uploadFiles]
            await asyncio.gather(*tasks, return_exceptions=True)

        metadata = {
            "output_format": outputFormat,
            "include_screenshots": includeScreenshots,
            "audience_context": audienceContext,
            "custom_prompt": customPrompt,
            "detail_level": detailLevel,
        }

        data = {
            "user_id": str(uuid.uuid4()),
            "video_id": str(uuid.uuid4()), # blob name
            "file_path": "submissions",
            "summary_type": summaryType,
            "params": metadata,
            "processing_timestamp": str(datetime.now()),
        }

        save_json(data=data)

        message = PubSubMessage(**data)

        # Render result template
        return templates.TemplateResponse(
            "results.html", {"request": request, "data": data}
        )

    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"error": str(e)}
