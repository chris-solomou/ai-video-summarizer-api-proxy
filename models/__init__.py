from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List, Optional

class Payload(BaseModel):
    user_id: int
    task :str
    params: Dict[str, Any]

class Metadata(BaseModel):
    summaryType: int
    customPrompt: Optional[str] = None
    audienceContext: Optional[str] = None
    includeScreenshots: bool
    outputFormat: str
    detailLevel: int

class PubSubMessage(BaseModel):
    video_id: str
    summary_type: str
    metadata: Dict[str, Any]
    processing_timestamp: datetime

class SignedUrlResponse(BaseModel):
    video_id: str
    signed_url: str

class SignedURLRequest(BaseModel):
    files: List[Dict[str, str]]
