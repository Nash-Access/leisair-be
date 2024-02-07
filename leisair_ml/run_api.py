from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
from leisair_ml.routers import file_upload, update
from leisair_ml.utils.file_watcher import start_watching, stop_watching
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_watching()
    # TODO: Load any necessary resources, like a YOLO model
    yield
    stop_watching()
    # TODO: Unload resources, like the YOLO model

allowed_origins = [
    "http://localhost:3000",
]

app = FastAPI()# (lifespan=lifespan)
app.include_router(file_upload.router)
app.include_router(update.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allows specified origins
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def main():
    uvicorn.run("leisair_ml.run_api:app", host="0.0.0.0", port=8000, reload=True)