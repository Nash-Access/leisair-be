from pydantic import BaseModel, Field, AfterValidator, PlainSerializer, WithJsonSchema
from typing import Dict, List, Literal, Optional, Annotated, Union
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

VesselTypes = Literal['Not Vessel','SUP','Kayak Or Canoe','Rowing Boat','Yacht','Sailing Dinghy','Narrow Boat','Uber Boat',' Class V Passenger','RIB','RNLI','Pleasure Boat', 'Small Powered','Workboat','Tug','Tug - Towing', 'Tug - Pushing','Large Shipping','Fire','Police']

class BBOX(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

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
    vesselId: str
    type: VesselTypes
    confidence: float
    speed: Optional[float]
    direction: Optional[str]
    bbox: BBOX


class CameraVideo(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    locationId: str
    filename: str
    startTime: datetime
    endTime: Optional[datetime]
    vesselsDetected: Optional[Dict[int, List[VesselDetected]]]
    # metadata: Optional[Dict]

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

def custom_alias_gen(field_name: str):
    if field_name == "_id":
        return "id"
    if field_name == "startTime":
        return "start_time"
    if field_name == "vesselId":
        return "vessel_id"
    return field_name

class VesselCorrections(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    filename: str
    start_time: datetime = Field(..., alias="startTime")
    frame: str
    type: VesselTypes
    vessel_id: str = Field(..., alias="vesselId")
    confidence: float
    bbox: BBOX
    speed: Optional[float]
    direction: Optional[str]
    image: str
    used: Optional[bool] = None

    class Config:
        json_encoders = {ObjectId: str}
        alias_generator = custom_alias_gen
        exclude_none = True
        populate_by_name = True
        arbitrary_types_allowed = True


class VesselDetectionModel(BaseModel):
    id: str = Field(None, alias="_id")
    name: str
    description: str
    modelPath: str
    weightsPath: str
    configPath: str
    classNames: List[str]

    class Config:
        json_encoders = {ObjectId: str}
        exclude_none = True
        populate_by_name = True
        arbitrary_types_allowed = True