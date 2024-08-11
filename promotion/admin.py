from django.contrib import admin

from .models import Type, Option, PaymentHistory


class OptionAdmin(admin.ModelAdmin):
    model = Option
    list_display = (
        "type",
        "term",
        "price",
    )


class OptionInline(admin.TabularInline):
    model = Option


class TypeAdmin(admin.ModelAdmin):
    model = Type
    list_display = (
        "name",
        "slug",
        "index",
    )
    inlines = (OptionInline,)


class PaymentHistoryAdmin(admin.ModelAdmin):
    model = PaymentHistory
    list_display = (
        "payment_intent",
        "user",
        "total_price",
        "created_at",
    )
    filter_horizontal = ("options",)


admin.site.register(Type, TypeAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(PaymentHistory, PaymentHistoryAdmin)
