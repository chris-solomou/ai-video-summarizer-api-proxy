from utils import generate_video_id, generate_signed_urls, verify_email_domain
import pytest
from google.cloud import storage
from services.gcp import StorageBucket
from typing import List, Dict


@pytest.mark.parametrize("filename", ["video.mp4", "document.pdf", "image.jpeg"])
def test_generate_file_id(filename: str):
    ext = filename.split(".")[-1]
    video_id = generate_video_id(file_name=filename)
    # test output format
    assert isinstance(video_id, str)
    # test file extention maintained from original file
    assert ext in video_id


@pytest.mark.parametrize(
    "files",
    [
        [
            {"filename": "video.mp4", "content_type": "video/mp4"},
            {"filename": "archive.tar.gz", "content_type": "application/gzip"},
        ]
    ],
)
def test_generate_signed_urls(files: List[Dict[str, str]]):
    BUCKET_NAME = "ai-video-summarizer-dev-bucket"
    storage_client = storage.Client()
    storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=storage_client)
    file_names = [file["filename"] for file in files]
    signed_urls = generate_signed_urls(
        file_names=file_names, storage_bucket=storage_bucket
    )
    for entry, file in zip(signed_urls, files):
        # file extention maintained in the signed url
        assert entry["video_id"].endswith(file["filename"].split(".")[-1])
        # bucket name is included in signed url
        assert BUCKET_NAME in entry["signed_url"]


@pytest.mark.parametrize(
    "file_id,exists",
    [
        ("007902be-9129-4950-a0a2-681ad703a6dc.png", True),
        ("18f3669d-7a3d-4bec-a83b-47abb99153b9.png", True),
        ("video_1234.mov", False),
    ],
)
def test_file_exists(file_id: str, exists: bool):
    BUCKET_NAME = "ai-video-summarizer-dev-bucket"
    storage_client = storage.Client()
    storage_bucket = StorageBucket(bucket_name=BUCKET_NAME, client=storage_client)
    assert storage_bucket.check_file_exists(file_id) == exists


@pytest.mark.parametrize(
    "email,valid",
    [
        ("mary.hill@productmadness.com", True),
        ("alex.smith@gmail.com", False),
        ("mary_andrews@yahoo.com", False),
        ("ben.davies@.aristocrat.com", False),
        ("ben.davies@aristocrat.com", True),
        ("laura_andrews.gmail.com", False),
        ("laura_andrews.productmadness.com", False),
    ],
)
def test_valid_email_domain(email: str, valid: bool):
    assert verify_email_domain(email) == valid
