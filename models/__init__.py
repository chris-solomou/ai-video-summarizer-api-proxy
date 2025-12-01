from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List, Optional

class FormData(BaseModel):
    video_ids: List[str]
    summaryType: int
    customPrompt: Optional[str] = None
    audienceContext: Optional[str] = None
    includeScreenshots: bool
    outputFormat: str
    detailLevel: int

class PubSubMessage(BaseModel):
    video_id: str
    metadata: Dict[str, Any]
    processing_timestamp: datetime

class SignedUrlResponse(BaseModel):
    video_id: str
    signed_url: str

class SignedURLRequest(BaseModel):
    files: List[Dict[str, str]]
