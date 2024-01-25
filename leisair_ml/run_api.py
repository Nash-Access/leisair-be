from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from leisair_ml.routers import api
from leisair_ml.utils.file_watcher import start_watching, stop_watching


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_watching()
    # TODO: Load any necessary resources, like a YOLO model
    yield
    stop_watching()
    # TODO: Unload resources, like the YOLO model


app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
