from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class Payload(BaseModel):
    user_id: int
    task :str
    params: Dict[str, Any]
    

class PubSubMessage(BaseModel):
    video_id: str
    summary_type: str
    params: Dict[str, Any]
    processing_timestamp: datetime