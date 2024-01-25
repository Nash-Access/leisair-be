import os


def main():
    os.system("celery -A leisair_ml.celery_worker worker --loglevel=info -E -P solo")
