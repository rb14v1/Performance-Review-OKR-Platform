import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("perf_okr_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Minimal, genuinely-needed beat schedule: deadline reminder emails for
# cycles approaching their end date, and (separately) feedback-request
# emails are sent immediately on creation, not on a schedule. Cycle STAGE
# transitions themselves are never auto-triggered by beat - the state
# machine's guard conditions (all manager reviews submitted, all
# calibration entries resolved, etc.) require a human decision, so only an
# HR admin calling POST /api/cycles/{id}/transition/ actually moves a
# cycle's status. This task is idempotent: it only ever *sends* reminder
# emails (guarded by a lookup of who has/hasn't submitted yet), it never
# mutates cycle state, so a scheduler restart cannot double-apply a
# transition.
app.conf.beat_schedule = {
    "send-cycle-deadline-reminders": {
        "task": "apps.notifications.tasks.send_cycle_deadline_reminders",
        "schedule": crontab(hour="7", minute="0"),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
