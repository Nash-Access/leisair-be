from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import asyncio

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.mp4'):  # Check for video file extension
            self.callback(event.src_path)

class FileWatcher:
    def __init__(self, path_to_watch, callback):
        self.path_to_watch = path_to_watch
        self.observer = Observer()
        self.event_handler = NewFileHandler(callback)

    def start(self):
        self.observer.schedule(self.event_handler, self.path_to_watch, recursive=False)
        self.observer.start()
        asyncio.create_task(self._run_forever())

    async def _run_forever(self):
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            # This exception will be raised when the asyncio task is cancelled
            pass

    def stop(self):
        self.observer.stop()
        self.observer.join()

async def trigger_fastapi_endpoint(file_path):
    # Trigger the FastAPI endpoint
    await requests.post('http://localhost:8000/detect', json={'file_path': file_path})

# Global instance of the FileWatcher
file_watcher = FileWatcher('/path/to/watch', trigger_fastapi_endpoint)

def start_watching():
    file_watcher.start()

def stop_watching():
    file_watcher.stop()
