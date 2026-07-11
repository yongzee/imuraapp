import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_tryon.settings")

app = Celery("my_tryon")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: ['apps.measureApp'])