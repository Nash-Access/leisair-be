from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.routers import api, websocket
from .file_watcher import start_watching, stop_watching  

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_watching('/path/to/watch') 
    # TODO: LOAD YOLO MODEL HERE
    yield
    stop_watching()
    # TODO: UNLOAD YOLO MODEL HERE


app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
app.include_router(websocket.router)

