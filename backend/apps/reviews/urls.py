from rest_framework.routers import DefaultRouter

from apps.reviews.views import (
    ManagerReviewViewSet,
    RatingViewSet,
    ReviewCycleViewSet,
    SelfReviewViewSet,
)

router = DefaultRouter()
router.register("cycles", ReviewCycleViewSet, basename="cycle")
router.register("self-reviews", SelfReviewViewSet, basename="self-review")
router.register("manager-reviews", ManagerReviewViewSet, basename="manager-review")
router.register("ratings", RatingViewSet, basename="rating")

urlpatterns = router.urls
