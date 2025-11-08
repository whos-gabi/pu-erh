"""
Celery configuration pentru procesarea asincronă a notificărilor.
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('office_appointments')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de debug pentru testare."""
    print(f'Request: {self.request!r}')

