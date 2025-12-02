from typing import Union
import uuid
from fastapi import UploadFile

def generate_video_id(file: Union[UploadFile, str]) -> str:
    if isinstance(file, UploadFile):
        file_name = file.filename
    elif isinstance(file, str):
        file_name = file
    else:
        raise TypeError(f"File of type {type(file)} is not supported!")
    ext = file_name.split(".")[-1]
    return str(uuid.uuid4()) + "." + ext