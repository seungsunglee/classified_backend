from audioop import reverse
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q, Count
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sorl.thumbnail import get_thumbnail, delete

import uuid


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    field_attributes = models.ManyToManyField(
        "Attribute", blank=True, related_name="field_attributes"
    )
    filter_attributes = models.ManyToManyField(
        "Attribute", blank=True, related_name="filter_attributes"
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    promotions = models.ManyToManyField("promotion.Type", blank=True)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "TEXT"
        INTEGER = "integer", "INTEGER"
        OPTION = "option", "OPTION"
        MULTIPLE_CHECKBOX = "multiple_checkbox", "MULTIPLE_CHECKBOX"
        BOOLEAN = "boolean", "BOOLEAN"
        RADIO = "radio", "RADIO"
        DATE = "date", "DATE"
        DECIMAL = "decimal", "DECIMAL"

    class FilterType(models.TextChoices):
        SELECT = "select", "SELECT"
        RANGE_INPUT = "range_input", "RANGE_INPUT"

    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    field_type = models.CharField(max_length=50, choices=FieldType.choices)
    required = models.BooleanField(default=False)
    filter_type = models.CharField(
        max_length=50, choices=FilterType.choices, null=True, blank=True
    )
    index = models.IntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        if self.note is not None:
            return "%s (%s)" % (self.name, self.note)
        else:
            return self.name


class Option(models.Model):
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    value = models.SlugField()

    def __str__(self):
        return self.name


class ItemQuerySet(models.QuerySet):
    def filter_by_query(self, query):
        queryset = self

        category_id = query.get("category_id")
        if category_id:
            queryset = queryset.filter(
                Q(category=category_id) | Q(category__parent=category_id)
            )

        location_id = query.get("location_id")
        if location_id:
            queryset = queryset.filter(
                Q(location=location_id) | Q(location__parent=location_id)
            )

        keyword = query.get("keyword")
        if keyword:
            valid_keyword = keyword.strip().split()
            title_query = Q()
            for k in valid_keyword:
                title_query = title_query & Q(title__icontains=k)
            description_query = Q()
            for k in valid_keyword:
                description_query = description_query & Q(description__icontains=k)
            queryset = queryset.filter(Q(title_query) | Q(description_query))

        min_deposit = query.get("min_deposit")
        if min_deposit and min_deposit.isdigit():
            if int(min_deposit) > 0:
                queryset = queryset.filter(attributes__deposit__gte=int(min_deposit))
        max_deposit = query.get("max_deposit")
        if max_deposit and max_deposit.isdigit():
            if int(max_deposit) > 0:
                queryset = queryset.filter(attributes__deposit__lte=int(max_deposit))
            else:
                queryset = queryset.filter(attributes__no_deposit=True)

        min_rent = query.get("min_rent")
        if min_rent and min_rent.isdigit():
            if int(min_rent) > 0:
                queryset = queryset.filter(attributes__rent__gte=int(min_rent))
        max_rent = query.get("max_rent")
        if max_rent and max_rent.isdigit():
            if int(max_rent) > 0:
                queryset = queryset.filter(attributes__rent__lte=int(max_rent))

        min_price = query.get("min_price")
        if min_price and min_price.isdigit():
            if int(min_price) > 0:
                queryset = queryset.filter(attributes__price__gte=int(min_price))
        max_price = query.get("max_price")
        if max_price and max_price.isdigit():
            if int(max_price) > 0:
                queryset = queryset.filter(attributes__price__lte=int(max_price))
            else:
                queryset = queryset.filter(attributes__no_price=True)

        sort = query.get("sort")
        if sort:
            if sort == "recommended":
                queryset = queryset.annotate(count=Count("bookmark")).order_by("-count")
            elif sort == "deposit_asc":
                queryset = queryset.order_by("attributes__deposit")
            elif sort == "deposit_desc":
                queryset = queryset.order_by("-attributes__deposit")
            elif sort == "rent_asc":
                queryset = queryset.order_by("attributes__rent")
            elif sort == "rent_desc":
                queryset = queryset.order_by("-attributes__rent")
            elif sort == "price_asc":
                queryset = queryset.order_by("attributes__price")
            elif sort == "price_desc":
                queryset = queryset.order_by("-attributes__price")

        return queryset

    def filter_by_fixed(self):
        return self.filter(promotion__type__slug="fixed").order_by("-updated_at")

    def filter_by_unfixed(self):
        return self.exclude(promotion__type__slug="fixed")

    def filter_by_related(self, instance):
        queryset = (
            self.filter(category__parent=instance.category.parent)
            .filter(location__parent_id=instance.location.parent)
            .exclude(id=instance.id)[:8]
        )
        return queryset


class Item(models.Model):
    author = models.ForeignKey(
        "authentication.User", verbose_name="投稿者", on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("カテゴリー"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(_("タイトル"), max_length=80)
    description = models.TextField(_("詳細"), max_length=3000)
    attributes = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    location = models.ForeignKey(
        "locations.Location", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(_("投稿日"), default=timezone.now)
    updated_at = models.DateTimeField(_("更新日"), default=timezone.now)

    views = models.IntegerField(default=0)

    objects = ItemQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('classifieds:detail', kwargs={'id': self.id})


class Promotion(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    type = models.ForeignKey(
        "promotion.Type", on_delete=models.SET_NULL, null=True, blank=True
    )
    disabled_at = models.DateTimeField(null=True, blank=True)


def image_directory_path(instance, filename):
    return "{}.{}".format(str(uuid.uuid4()), filename.split(".")[-1])


class Image(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    index = models.IntegerField(null=True, blank=True)
    file = models.ImageField(upload_to=image_directory_path, null=True, blank=True)
    temp_id = models.UUIDField(default=uuid.uuid4, null=True, blank=True)

    class Meta:
        ordering = ["index"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            tmp_file_name = self.file.name
            if self.file.width > 600 or self.file.height > 600:
                new_width = 600
                new_height = 600

                resized = get_thumbnail(
                    self.file, "{}x{}".format(new_width, new_height)
                )
                name = resized.name.split("/")[-1]
                self.file.save(name, ContentFile(resized.read()), True)
                delete(tmp_file_name)


@receiver(pre_delete, sender=Image)
def delete_image(sender, instance, **kwargs):
    delete(instance.file.name)
