import os


def launch_worker():
    os.system("celery -A celery_worker worker --loglevel=info -E -P solo")
