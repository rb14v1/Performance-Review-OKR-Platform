"""
Settings used by `manage.py test`. Forces SQLite + eager Celery regardless
of the environment so `python manage.py test --settings=config.settings.test`
is reproducible on a machine with no Postgres/Redis, and so Celery-backed
notification logic (deadline reminders, feedback-request emails) actually
runs synchronously inside the tests that exercise it.
"""
from .base import *  # noqa: F401,F403

DEBUG = False
USE_SQLITE = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test-sqlite.db",  # noqa: F405
    }
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
