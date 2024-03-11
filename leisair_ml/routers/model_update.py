import logging
from fastapi import APIRouter, Response, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from leisair_ml.celery_worker import retrain_model
from pathlib import Path
import os

router = APIRouter()
logger = logging.getLogger("leisair")

VIDEOS_PATH = os.environ.get("VIDEOS_PATH", "C:/Users/ayman/OneDrive - Brunel University London/PhD/NASH Project/mount-dir/cctv-videos")

@router.post("/update-model")
async def update_model(response: Response):
    try:
        retrain_model.delay()
        
        return {"message": "Model update started."}
    except Exception as e:
        logger.error("Error updating model:", e)
        raise HTTPException(status_code=500, detail="Error updating model.")