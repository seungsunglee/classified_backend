from django.db import models
from django.contrib import admin

from .models import Option, Attribute, Category, Item, Promotion, Image

from django_json_widget.widgets import JSONEditorWidget

from sorl.thumbnail.admin import AdminImageMixin


class OptionInline(admin.TabularInline):
    model = Option


class OptionAdmin(admin.ModelAdmin):
    list_display = (
        "attribute",
        "name",
        "value",
    )
    list_display_links = ("name",)
    ordering = ("id",)


class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display = (
        "name",
        "slug",
        "field_type",
        "required",
        "filter_type",
        "index",
        "note",
    )
    inlines = (OptionInline,)


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parent",
        "name",
        "level",
        "title",
    )
    list_display_links = ("name",)
    filter_horizontal = (
        "field_attributes",
        "filter_attributes",
        "promotions",
    )
    ordering = ("id",)

    list_select_related = ["parent"]


class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 1


class ImageInline(admin.TabularInline):
    model = Image


class PromotionAdmin(admin.ModelAdmin):
    model = Promotion
    list_display = (
        "type",
        "item",
        "disabled_at",
    )


class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "location",
        "updated_at",
    )
    autocomplete_fields = ["location"]
    inlines = (
        PromotionInline,
        ImageInline,
    )
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(height="300px")}
    }

    list_select_related = ("category", "location")


class ImageAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "temp_id",
        "file",
        "item",
    )


admin.site.register(Option, OptionAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Promotion, PromotionAdmin)
admin.site.register(Image, ImageAdmin)
