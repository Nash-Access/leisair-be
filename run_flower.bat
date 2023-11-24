celery -A celery_worker flower --port=5555 --broker=redis://localhost:6379/1 --loglevel=debug 
