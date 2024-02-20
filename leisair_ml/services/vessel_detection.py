
from datetime import datetime
from pathlib import Path
from datetime import datetime
import logging
import supervision as sv
from supervision import ByteTrack
from ultralytics.data.loaders import LoadImages
from ultralytics import YOLO

from leisair_ml.utils.logger import custom_logger
from leisair_ml.utils.mongo_handler import MongoDBHandler
from leisair_ml.schemas import CameraLocation, CameraVideo, VesselDetected
# Initialize logger
LOGGER = logging.getLogger("leisair")

# Initialize MongoDB handler
mongo_handler = MongoDBHandler()



def check_and_create_location(filename: str) -> str:
    location_name = filename.split(" ")[0]
    existing_location = mongo_handler.read_camera_location_by_name(location_name)
    if existing_location:
        return str(existing_location.id) if existing_location.id else ""
    else:
        LOGGER.info("NAME: %s", location_name)
        new_location = CameraLocation(_id=None, name=location_name, latitude=0.0, longitude=0.0)
        location_id = mongo_handler.create_camera_location(new_location)
        LOGGER.info("LOCATION ID: %s", location_id)
        return str(location_id)

def create_camera_video_entry(filename: str, location_id: str):
    datetime_format = "%Y-%m-%d_%H_%M_%S_%f"
    time = datetime.strptime(filename.split(" ")[1], datetime_format)
    LOGGER.info(f"TIME: {time}, LOCATION ID:{location_id}, FILENAME:{filename}")
    try:
        new_video = CameraVideo(_id=None, locationId=location_id, filename=filename, startTime=time, endTime=None, vesselsDetected={})
        video_id = mongo_handler.create_camera_video(new_video)
        mongo_handler.create_video_status(video_id, filename, "processing", 0.0)
        return video_id
    except ValueError as e:
        LOGGER.error(f"Error creating CameraVideo: {e}")
        print(f"Error details: {e}")
        return None

def run_supervision(video_frame, model, byte_tracker:ByteTrack):
    results = model(video_frame)[0]
    results.obb = None
    detections = sv.Detections.from_ultralytics(results)
    detections = byte_tracker.update_with_detections(detections)
    bboxes_this_frame = [
        {
            "tracker_id": tracker_id,
            "class_id": class_id,
            "confidence": confidence,
            "bbox": {"x1": float(xyxy[0]), "y1": float(xyxy[1]), "x2": float(xyxy[2]), "y2": float(xyxy[3])}
        }
        for xyxy, _, confidence, class_id, tracker_id, _ in detections
    ]
    return bboxes_this_frame

def run(weights: Path, source: Path):
    # Initialize model, byte_tracker, and annotator
    model = YOLO(weights)
    class_name_dict = model.names
    if not class_name_dict:
        LOGGER.error("Error loading class names")
        return
    byte_tracker = sv.ByteTrack()
    
    video_filename = source.stem
    location_id = check_and_create_location(video_filename)
    video_id = create_camera_video_entry(video_filename, location_id)
    if not video_id:
        LOGGER.error("Error creating CameraVideo entry")
        return

    vesselsDetected = {}

    dataset = LoadImages(source, imgsz=640, vid_stride=1)
    for idx, (_, img, _, _) in enumerate(dataset):
        print(f"\n---------Processing frame {idx+1}/{dataset.frames}---------")
        video_frame = img 
        detections = run_supervision(video_frame, model, byte_tracker)
        for detection in detections:
            vessel_detected = VesselDetected(
                vesselId=str(detection["tracker_id"]),
                type=class_name_dict[detection["class_id"]],
                confidence=float(detection["confidence"]),
                speed=None,
                direction=None,
                bbox=detection["bbox"]
            )
            print(f"Vessel detected: {vessel_detected}")
            if str(idx) not in vesselsDetected:
                vesselsDetected[str(idx)] = []
            vesselsDetected[str(idx)].append(vessel_detected)
        progress = (idx / dataset.frames) * 100.0
        mongo_handler.update_video_status(video_id, "processing", progress)

    mongo_handler.update_vessels_detected_bulk(video_id, vesselsDetected)
    mongo_handler.update_video_status(video_id, "done", 100.0)