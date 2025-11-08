"""
Django project initialization.
"""
# Import Celery app pentru a-l încărca când Django pornește
from .celery import app as celery_app

__all__ = ('celery_app',)

