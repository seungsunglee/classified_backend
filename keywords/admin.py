from django.contrib import admin
from .models import Keyword


@admin.action(description="選択した項目を確認済みにする")
def make_confirmed(modeladmin, request, queryset):
    queryset.update(confirmed=True)


class KeywordAdmin(admin.ModelAdmin):
    list_display = ("title", "roman_alphabet", "confirmed")
    actions = [make_confirmed]


admin.site.register(Keyword, KeywordAdmin)
