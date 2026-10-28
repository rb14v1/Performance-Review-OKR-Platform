from rest_framework.routers import DefaultRouter

from apps.feedback.views import (
    CalibrationEntryViewSet,
    CalibrationSessionViewSet,
    FeedbackRequestViewSet,
    PeerFeedbackViewSet,
)

router = DefaultRouter()
router.register("feedback-requests", FeedbackRequestViewSet, basename="feedback-request")
router.register("peer-feedback", PeerFeedbackViewSet, basename="peer-feedback")
router.register("calibration-sessions", CalibrationSessionViewSet, basename="calibration-session")
router.register("calibration-entries", CalibrationEntryViewSet, basename="calibration-entry")

urlpatterns = router.urls
