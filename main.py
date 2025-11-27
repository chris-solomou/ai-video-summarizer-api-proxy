from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from models import PubSubMessage, SignedURLRequest
from fastapi.staticfiles import StaticFiles
import asyncio
from google.cloud import storage
from sources.gcp import StorageBucket

def generate_video_id(file: UploadFile) -> str:
    file_name = file.filename
    ext = file_name.split(".")[-1]
    return str(uuid.uuid4()) + "." + ext



BUCKET_NAME = "ai-video-summarizer-dev-bucket"
client = storage.Client()
input_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=client)

"""
curl -X POST "  /params" \
     -H "Content-Type: multipart/form-data" \
     -F "user_id=123" \
     -F "task=process" \
     -F "params={}" \
     -F "file=@/Users/chris.solomou/Downloads/Screenshot 2025-11-11 at 11.55.08.png"
"""


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
        user_id = str(uuid.uuid4())

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
                "user_id": user_id,
                "video_ids": [],
                "file_paths": [],
                "summary_type": summaryType,
                "params": metadata,
                "processing_timestamp": str(datetime.now()),
            }

        for file in uploadFiles:
            video_id = generate_video_id(file)

            message = PubSubMessage(
                video_id=video_id,
                summary_type=summaryType,
                params=metadata,
                processing_timestamp=str(datetime.now())
            ).dict()

            file.file.seek(0)
            file_path = input_bucket.upload_file_to_bucket(
                upload_file=file, blob_name=video_id
            )

            data["video_ids"].append(video_id)
            data["file_paths"].append(file_path)

        

        # Render result template
        return templates.TemplateResponse(
            "results.html", {"request": request, "data": data}
        )

    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"error": str(e)}
