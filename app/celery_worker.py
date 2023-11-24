import time
from celery import Celery
from celery.utils.log import get_task_logger
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

# Configure Celery to use Redis as the broker and result backend
celery_app = Celery("my_worker", 
                    broker="redis://localhost:6379/0", 
                    backend="redis://localhost:6379/0")

# Update Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_expires=3600,  # Results expire after 1 hour
    worker_concurrency=1,  # Only one worker per container
    worker_log_color=False,
    worker_hijack_root_logger=False,
    accept_content=['json'],  # Accept JSON content only
)

@celery_app.task(bind=True)
def process_file(self, file_path: str):
    print(f"Starting task: {self.request.id}")  # Debug print
    time.sleep(30)
    logger.info(f"(Celery) Processing file: {file_path}")
    with open("TEST.txt", "a") as f:
        f.write(f"Processing file: {file_path}\n")
    # Place your file processing logic here
    # You can use 'self' to access task context like 'self.request.id' for the task ID  
