import asyncio
import os
import queue
import httpx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.mp4'):
            self.queue.put(event.src_path)

class FileWatcher:
    def __init__(self, path_to_watch, process_file_callback):
        self.path_to_watch = path_to_watch
        self.process_file_callback = process_file_callback
        self.thread_safe_queue = queue.Queue()
        self.observer = Observer()
        self.observer.schedule(NewFileHandler(self.thread_safe_queue), self.path_to_watch, recursive=False)

    def start(self):
        self.observer.start()
        asyncio.create_task(self._process_files())

    async def _process_files(self):
        while True:
            file_path = await asyncio.to_thread(self.thread_safe_queue.get)
            await self.process_file_callback(file_path)

    def stop(self):
        self.observer.stop()
        self.observer.join()

async def process_file(file_path):
    print("Starting detection on file: ", file_path)
    abs_file_path = os.path.abspath(file_path)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post('http://localhost:8000/detect', json={'file_path': abs_file_path}, timeout=10)
            response.raise_for_status()
            print(response.json())
    except httpx.HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url}.")
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url}.")

def start_watching():
    file_watcher.start()

def stop_watching():
    file_watcher.stop()

file_watcher = FileWatcher('./data', process_file)


# import asyncio
# import os
# import queue
# import requests
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# class NewFileHandler(FileSystemEventHandler):
#     def __init__(self, queue):
#         self.queue = queue

#     def on_created(self, event):
#         if not event.is_directory and event.src_path.endswith('.mp4'):
#             self.queue.put(event.src_path)

# class FileWatcher:
#     def __init__(self, path_to_watch, process_file_callback):
#         self.path_to_watch = path_to_watch
#         self.process_file_callback = process_file_callback
#         self.thread_safe_queue = queue.Queue()
#         self.observer = Observer()
#         self.observer.schedule(NewFileHandler(self.thread_safe_queue), self.path_to_watch, recursive=False)

#     def start(self):
#         self.observer.start()
#         asyncio.create_task(self._process_files())

#     async def _process_files(self):
#         while True:
#             file_path = await asyncio.to_thread(self.thread_safe_queue.get)
#             await self.process_file_callback(file_path)

#     def stop(self):
#         self.observer.stop()
#         self.observer.join()

# async def process_file(file_path):
#     print("Starting detection on file: ", file_path)
#     abs_file_path = os.path.abspath(file_path)
#     response = await requests.post('http://localhost:8000/detect', json={'file_path': abs_file_path},timeout=10)
#     print(response.json())

# # async def process_file(file_path):
# #     print("Starting detection on file: ", file_path)
# #     async with httpx.AsyncClient() as client:
# #         try:
# #             response = await client.post('http://localhost:8000/detect', json={'file_path': file_path}, timeout=10)
# #             # Handle response if necessary
# #         except httpx.ReadTimeout:
# #             print("Request to /detect timed out.")

# # Usage
# file_watcher = FileWatcher('./data', process_file)


