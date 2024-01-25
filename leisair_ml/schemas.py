from pydantic import BaseModel, Field, AfterValidator, PlainSerializer, WithJsonSchema
from typing import Dict, List, Optional, Annotated, Union
from bson.objectid import ObjectId
from datetime import datetime


# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid ObjectId")
#         return ObjectId(v)

#     @classmethod
#     def __get_pydantic_json_schema__(cls, field_schema):
#         field_schema.update(type="string")


def validate_object_id(v: Union[str, ObjectId]) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[
    Union[str, ObjectId],
    AfterValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class CameraLocation(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    latitude: float
    longitude: float

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        exclude_none = True
        arbitrary_types_allowed = True


class VesselDetected(BaseModel):
    type: str = Field(
        ...,
        description="'Kayak or Canoe' | 'RIB' | 'Rowing' | 'SUP' | 'Small Unpowered' | 'Small Powered' | 'Tug' | 'Passenger'",
    )
    confidence: float
    speed: Optional[float]
    direction: Optional[str]
    bbox: dict


class CameraVideo(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    locationId: str
    filename: str
    startTime: datetime
    endTime: Optional[datetime]
    vesselsDetected: Optional[Dict[int, List[VesselDetected]]]
    metadata: Optional[Dict]

    class Config:
        json_encoders = {ObjectId: str}
        exclude_none = True
        populate_by_name = True
        arbitrary_types_allowed = True


class VideoStatus(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    filename: str
    status: str
    progress: float
    createdAt: datetime
    updatedAt: Optional[datetime]

    class Config:
        json_encoders = {ObjectId: str}
        exclude_none = True
        populate_by_name = True
        arbitrary_types_allowed = True
