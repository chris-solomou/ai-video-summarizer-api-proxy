from typing import List, Dict
import uuid
from sources.gcp import StorageBucket

def generate_video_id(file_name: str) -> str:
    ext = file_name.split(".")[-1]
    return str(uuid.uuid4()) + "." + ext

def generate_signed_urls(file_names: List[str], storage_bucket:StorageBucket) -> List[Dict[str,str]]:
    signed_urls = []
    for file_name in file_names:
        try:
            video_id = generate_video_id(file_name = file_name)
            signed_url = storage_bucket.generate_dummy_signed_url(blob_name = video_id)
            signed_urls.append({"video_id": video_id, "signed_url": signed_url})
        except Exception as e:
            print(f"The following exception has occurred {e}!")
        return signed_urls

print(generate_video_id("file.mp34"))