# routers/detection.py
from fastapi import APIRouter
from pydantic import BaseModel
from leisair_ml.celery_worker import process_file

router = APIRouter()


class DetectionRequest(BaseModel):
    file_path: str


@router.post("/detect")
async def process_vido(request: DetectionRequest):
    print("Received request to detect file: ", request.file_path)
    process_file.delay(request.file_path)
    return {"message": "Detection started"}
