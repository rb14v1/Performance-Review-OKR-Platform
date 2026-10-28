from rest_framework.routers import DefaultRouter

from apps.okrs.views import CheckInViewSet, KeyResultViewSet, ObjectiveViewSet

router = DefaultRouter()
router.register("objectives", ObjectiveViewSet, basename="objective")
router.register("key-results", KeyResultViewSet, basename="key-result")
router.register("check-ins", CheckInViewSet, basename="check-in")

urlpatterns = router.urls
