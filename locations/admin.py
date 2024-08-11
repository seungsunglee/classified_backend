from django.contrib import admin

from .models import Location


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "state_code",
        "id",
        "parent",
        "level",
    )
    search_fields = [
        "name",
    ]

    list_select_related = ["parent"]


admin.site.register(Location, LocationAdmin)
