import asyncio
from fastapi import APIRouter, WebSocket
from mongo_handler import MongoDBHandler

router = APIRouter()

# Initialize MongoDBHandler
mongo_handler = MongoDBHandler()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Fetch the latest statuses from MongoDB using MongoDBHandler
        statuses = await mongo_handler.get_all_videos()
        await websocket.send_json([status.dict() for status in statuses])
        await asyncio.sleep(1)  # Sleep time between sending messages
