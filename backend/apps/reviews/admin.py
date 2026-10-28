from django.contrib import admin

from apps.reviews.models import CycleStatusAudit, ManagerReview, Rating, ReviewCycle, SelfReview

admin.site.register(ReviewCycle)
admin.site.register(CycleStatusAudit)
admin.site.register(SelfReview)
admin.site.register(ManagerReview)
admin.site.register(Rating)
