from django.contrib import admin
from .models import Thread, Participant, Response


class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thread",
        "user",
        "last_response",
        "is_read",
        "updated_at",
        "is_deleted",
    )


class ParticipantInline(admin.TabularInline):
    model = Participant


class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "participants")
    inlines = (ParticipantInline,)

    list_select_related = ["item"]

    @admin.display
    def participants(self, obj):
        return list(obj.participant_set.values_list("user__username", flat=True))


class ResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thread",
        "sender",
        "receiver",
        "created_at",
    )
    ordering = ["-created_at"]


admin.site.register(Thread, ThreadAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Response, ResponseAdmin)
