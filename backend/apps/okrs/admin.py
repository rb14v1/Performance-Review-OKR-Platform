from django.contrib import admin

from apps.okrs.models import CheckIn, KeyResult, Objective

admin.site.register(Objective)
admin.site.register(KeyResult)
admin.site.register(CheckIn)
