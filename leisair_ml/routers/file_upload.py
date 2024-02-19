from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from leisair_ml.celery_worker import process_file
from pathlib import Path
import os

router = APIRouter()

VIDEOS_PATH = os.environ.get("VIDEOS_PATH", "C:/Users/ayman/OneDrive - Brunel University London/PhD/NASH Project/mount-dir/cctv-videos")

@router.post("/upload")
async def process_video(file: UploadFile = File(...)):
    # Check if the uploaded file is empty
    if file == None or file.filename is None or file.filename == "":
        raise HTTPException(status_code=400, detail="Empty file")

    # Generate a file path
    file_path = Path(VIDEOS_PATH) / file.filename
    
    # Check if file already exists to avoid overwriting
    if file_path.exists():
        raise HTTPException(status_code=400, detail="File already exists")

    # Save the uploaded file
    with file_path.open("wb") as buffer:
        while content := await file.read(1024):  # Adjust chunk size as needed
            buffer.write(content)

    await file.seek(0)
    
    print("Received request to detect file: ", file.filename)
    # Send the file to the Celery worker for processing
    process_file.delay(str(file_path))
    
    return {"message": "File queued for processing"}
