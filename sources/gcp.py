from fastapi import UploadFile
from google.cloud import storage
from typing import Optional, Dict, Any
from datetime import timedelta, datetime 
from google.cloud import pubsub_v1
import json
import urllib.parse
import uuid
from google.cloud.exceptions import GoogleCloudError


class StorageBucket:
    def __init__(self, bucket_name: str, client=Optional[storage.client]):
        self.bucket_name = bucket_name
        self.client = client or storage.Client()

    def __repr__(self):
        return f"<StorageBucket(bucket_name='{self.bucket_name}')>"

    def check_file_exists(self, blob_name : str) -> bool:
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
        
    def upload_file_to_bucket(
        self, upload_file: UploadFile, blob_name: str = None
    ) -> str:

        try:
            bucket = self.client.bucket(self.bucket_name)

            blob = bucket.blob(blob_name)
            blob.upload_from_file(
                upload_file.file, content_type=upload_file.content_type
            )
        
        except Exception as e:
            print(f"The following exception has occurred! {e}")
            raise

        # final storage file path
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
    
    def generate_dummy_signed_url(blob_name: str) -> str:
        """
        Return a fake signed URL for local development.
        Shape matches GCP v4 signed URLs, but contains no real signature.
        """
        expiration = int((datetime.utcnow() + timedelta(minutes=15)).timestamp())

        fake_signature = uuid.uuid4().hex
        fake_access_id = "dummy-service-account@example.iam.gserviceaccount.com"

        params = {
            "X-Goog-Algorithm": "GOOG4-RSA-SHA256",
            "X-Goog-Credential": fake_access_id,
            "X-Goog-Date": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
            "X-Goog-Expires": str(15 * 60),
            "X-Goog-SignedHeaders": "host",
            "X-Goog-Signature": fake_signature,
        }

        query = urllib.parse.urlencode(params)

        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}?{query}"
    

class PubSubPublisher:
    def __init__(
        self,
        pubsub_topic: str,
        publisher: Optional[pubsub_v1.PublisherClient] = None,
    ):
        self.topic = pubsub_topic
        self.publisher = publisher or pubsub_v1.PublisherClient()
    
    def __repr__(self):
        return f"<PubSubPublisher(topic='{self.topic}')>"

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