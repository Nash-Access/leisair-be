import time
from celery import Celery
from celery.utils.log import get_task_logger
import logging
from services.vessel_detection import main, run
from pathlib import Path


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

# Configure Celery to use Redis as the broker and result backend
celery_app = Celery("nash_worker", broker="amqp://localhost:5672/")

# Update Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_expires=3600,  # Results expire after 1 hour
    worker_log_color=False,
    worker_hijack_root_logger=False,
    accept_content=["json"],  # Accept JSON content only
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="tasks.process_file", bind=True)
def process_file(self, file_path: str):
    logger.info("Starting to process file: %s", file_path)
    run(
        weights="./model/best.pt",
        source=file_path,
        data="./model/LEISair 03_11_23 all classes.yaml",
    )
