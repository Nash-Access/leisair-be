from motor.motor_asyncio import AsyncIOMotorClient
from schemas import VideoStatus
from bson import ObjectId


class MongoDBHandler:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db["cameraVideo"]

    async def create_video(self, video_data: VideoStatus) -> VideoStatus:
        video = video_data.model_dump(by_alias=True)
        result = await self.collection.insert_one(video)
        video["file_id"] = result.inserted_id
        return VideoStatus(**video)

    async def get_video(self, file_id: str) -> VideoStatus:
        video = await self.collection.find_one({"_id": ObjectId(file_id)})
        return VideoStatus(**video) if video else None

    async def update_video(self, file_id: str, update_data: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(file_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_video(self, file_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0

    async def get_all_videos(self) -> list:
        videos = await self.collection.find().to_list(None)
        return [VideoStatus(**video) for video in videos]
