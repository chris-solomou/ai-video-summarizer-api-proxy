from fastapi import UploadFile
from google.cloud import storage
from typing import Optional, Dict, Any
from datetime import timedelta
from google.cloud import pubsub_v1
import json


class StorageBucket:
    def __init__(self, bucket_name: str, client=Optional[storage.client]):
        self.bucket_name = bucket_name
        self.client = client or storage.Client()

    def __repr__(self):
        return f"<StorageBucket(bucket_name='{self.bucket_name}')>"

    def upload_file_to_bucket(
        self, upload_file: UploadFile, blob_name: Optional[str] = None
    ) -> str:

        try:
            if not blob_name:
                blob_name = self.generate_blob_name()

            bucket = self.client.bucket(self.bucket_name)

            blob = bucket.blob(blob_name)
            blob.upload_from_file(
                upload_file.file, content_type=upload_file.content_type
            )
            # print("File saved successfully to bucket!")

        except Exception as e:
            raise e

        # storage file path
        return f"gs://{self.bucket_name}/{blob_name}"

    def generate_upload_signed_url(self, blob_name: str, method: str) -> str:
        if method not in ["GET", "POST", "PUT", "DELETE"]:
            raise ValueError(f"{method} not supported!")

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method=method,
            content_type="application/octet-stream",
        )
        return url
    

class PubSubPublisher:
    def __init__(
        self,
        pubsub_topic: str,
        publisher: Optional[pubsub_v1.PublisherClient] = None,
    ):
        self.topic = pubsub_topic
        self.publisher = publisher or pubsub_v1.PublisherClient()

    def publish_message(self, message: Dict[str, Any]) -> bool:
        try:
            future = self.publisher.publish(
                self.topic, json.dumps(message).encode("utf-8")
            )
            future.result()  # Wait for the publish to complete
            return True
        except Exception as e:
            print(f"Failed to publish the message with exception {e}")
            return False
