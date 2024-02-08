import datetime
import logging
import os
import re
import threading
from leisair_ml.schemas import (
    CameraLocation,
    CameraVideo,
    VesselDetected,
    VideoStatus,
)
from bson.objectid import ObjectId
from typing import Optional, List, Dict, Union
from pymongo.database import Database
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

custom_logger = logging.getLogger("leisair")


class MongoDBHandler:
    """
    Singleton class for handling MongoDB operations.

    Attributes:
    ----------
        _instance (MongoDBHandler): The singleton instance of the class.
        _lock (threading.Lock): Lock object for thread-safe singleton instantiation.
    """

    _instance: Optional['MongoDBHandler'] = None
    _lock: threading.Lock = threading.Lock()
    
    # Explicitly type attributes that will be set after __new__
    client: MongoClient
    db: Database

    def __new__(cls) -> 'MongoDBHandler':
        """
        Create a new instance of MongoDBHandler if it doesn't exist; otherwise, return the existing instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/ApexDev")
                    try:
                        instance = super(MongoDBHandler, cls).__new__(cls)
                        instance.client = MongoClient(connection_string)
                        instance.db = instance.client.get_database()
                        cls._instance = instance
                    except Exception as e:
                        custom_logger.critical(f"Could not connect to MongoDB: {e}")
                        raise
        if cls._instance is None:
            raise Exception("Failed to create MongoDBHandler instance")
        return cls._instance

    def _get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.
        """
        return self.db[collection_name]

    # CRUD operations for CameraLocation
    def create_camera_location(self, location: CameraLocation) -> Union[str,None]:
        """
        Create a new camera location.
        """
        collection = self._get_collection("cameraLocation")
        print("Inserting:", location.model_dump(by_alias=True))
        try:
            result = collection.insert_one(
                location.model_dump(by_alias=True, exclude_none=True)
            )
            print(f"Created camera location: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print("Error while inserting:", e)
            return None

    def read_camera_location(self, location_id: str) -> Union[CameraLocation, None]:
        """
        Read a camera location by ID.
        """
        collection = self._get_collection("cameraLocation")
        document = collection.find_one({"_id": ObjectId(location_id)})
        return CameraLocation(**document) if document else None

    def read_camera_location_by_name(self, name: str) -> Union[CameraLocation, None]:
        collection = self._get_collection("cameraLocation")
        document = collection.find_one({"name": name})
        if document:
            custom_logger.info(f"Found camera location: {document}")
            return CameraLocation(**document)
        return None

    def update_camera_location(self, location_id: str, update_data: Dict) -> bool:
        """
        Update a camera location.
        """
        collection = self._get_collection("cameraLocation")
        result = collection.update_one(
            {"_id": ObjectId(location_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_camera_location(self, location_id: str) -> bool:
        """
        Delete a camera location.
        """
        collection = self._get_collection("cameraLocation")
        result = collection.delete_one({"_id": ObjectId(location_id)})
        return result.deleted_count > 0

    # CRUD operations for CameraVideo
    def create_camera_video(self, video: CameraVideo) -> str:
        """
        Create a new camera video.
        """
        collection = self._get_collection("cameraVideo")
        result = collection.insert_one(
            video.model_dump(by_alias=True, exclude_none=True)
        )
        return str(result.inserted_id)

    def read_camera_video(self, video_id: str) -> Union[CameraVideo, None]:
        """
        Read a camera video by ID.
        """
        collection = self._get_collection("cameraVideo")
        document = collection.find_one({"_id": ObjectId(video_id)})
        return CameraVideo(**document) if document is not None else None

    def update_camera_video(self, video_id: str, update_data: Dict) -> bool:
        """
        Update a camera video.
        """
        collection = self._get_collection("cameraVideo")
        result = collection.update_one(
            {"_id": ObjectId(video_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    def update_vessels_detected_bulk(
        self, video_id: str, vessels_detected: Dict[int, List[VesselDetected]]
    ) -> bool:
        """
        Bulk update the vesselsDetected field of a cameraVideo document.
        """
        collection = self._get_collection("cameraVideo")

        vessels_detected_dict = {
            frame: [vessel.model_dump() for vessel in vessels]
            for frame, vessels in vessels_detected.items()
        }

        # Prepare the update data
        update_data = {"vesselsDetected": vessels_detected_dict}

        # Update the document
        result = collection.update_one(
            {"_id": ObjectId(video_id)}, {"$set": update_data}
        )
        print("Modified count:", result.modified_count)
        return result.modified_count > 0

    def delete_camera_video(self, video_id: str) -> bool:
        """
        Delete a camera video.
        """
        collection = self._get_collection("cameraVideo")
        result = collection.delete_one({"_id": ObjectId(video_id)})
        return result.deleted_count > 0

    # CRUD operations for VideoStatus
    def create_video_status(
        self, video_id: str, filename: str, status: str, progress: float
    ) -> str:
        """
        Create a new video status entry.
        """
        collection = self._get_collection("videoStatus")
        new_status = VideoStatus(
            _id=video_id,
            filename=filename,
            status=status,
            progress=progress,
            createdAt=datetime.datetime.now(),
            updatedAt=None,
        )
        result = collection.insert_one(
            new_status.model_dump(by_alias=True, exclude_none=True)
        )
        return str(result.inserted_id)

    def read_video_status(self, status_id: str) -> Union[VideoStatus, None]:
        """
        Read a video status by ID.
        """
        collection = self._get_collection("videoStatus")
        document = collection.find_one({"_id": ObjectId(status_id)})
        return VideoStatus(**document) if document else None

    def update_video_status(self, id: str, status: str, progress: float) -> bool:
        """
        Update an existing video status entry.
        """
        collection = self._get_collection("videoStatus")
        update_data = {
            "status": status,
            "progress": progress,
            "updatedAt": datetime.datetime.now(),
        }
        result = collection.update_one(
            {"_id": id},  # Assuming video_id is the filename
            {"$set": update_data},
        )
        return result.modified_count > 0

    def delete_video_status(self, status_id: str) -> bool:
        """
        Delete a video status.
        """
        collection = self._get_collection("videoStatus")
        result = collection.delete_one({"_id": ObjectId(status_id)})
        return result.deleted_count > 0

    # Other operations

    def get_all_camera_locations(self) -> List[CameraLocation]:
        """
        Get all camera locations.
        """
        collection = self._get_collection("cameraLocation")
        documents = collection.find()
        return [CameraLocation(**document) for document in documents]
