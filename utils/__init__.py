from typing import List, Dict, Union, Any
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from services.gcp import StorageBucket

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

def verify_jwt_token(token: str, secret_key: str, algorithm: str) -> Union[Dict[str,Any],None]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm], options={"require": ["exp"]})
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None

def verify_email_domain(email:str) -> bool:
    if "@" not in email:
        return False
    email_ext = email.split("@")[1].strip()
    if email_ext not in ["productmadness.com","aristocrat.com"]:
        return False
    return True

def create_jwt(email: str,name:str,secret_key: str, algorithm: str, expires_in_minutes=60) -> Dict[str,Any]:
    payload = {
        "sub": email,
        "name":name,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)
