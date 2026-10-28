from django.contrib import admin

from apps.feedback.models import (
    CalibrationEntry,
    CalibrationSession,
    FeedbackRequest,
    PeerFeedback,
    PeerFeedbackAccessLog,
)

admin.site.register(FeedbackRequest)
admin.site.register(PeerFeedback)
admin.site.register(PeerFeedbackAccessLog)
admin.site.register(CalibrationSession)
admin.site.register(CalibrationEntry)
