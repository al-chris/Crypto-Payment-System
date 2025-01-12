# app/celery_app.py

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.transaction_monitor"],
)


# Configure Celery
celery.conf.update(
    broker_connection_retry_on_startup=True,  # Address the deprecation warning
    beat_schedule={
        'monitor-transactions-every-minute': {
            'task': 'app.tasks.transaction_monitor.monitor_transactions',
            'schedule': 60.0,  # Every 60 seconds
        },
    },
    timezone='UTC'
)