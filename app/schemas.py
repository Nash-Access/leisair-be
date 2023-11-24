from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, v):
        return {"type": "string", "format": "objectid"}

class VideoStatus(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    filename: str
    status: str
    progress: float
    history: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime]


    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        json_schema_extra = {
            "example": {
                "filename": "example_video.mp4",
                "status": "processing",
                "progress": 50.0,
                "history": ["uploaded", "processing"],
            }
        }

class VesselDetection(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cameraId: str
    x1: int
    y1: int
    x2: int
    y2: int
    classification: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float
    direction: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        json_schema_extra = {
            "example": {
                "cameraId": "camera1",
                "x1": 0,
                "y1": 0,
                "x2": 100,
                "y2": 100,
                "classification": "vessel",
                "timestamp": "2020-01-01T00:00:00Z",
                "confidence": 0.9,
                "direction": "East",
            }
        }