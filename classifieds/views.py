from collections import OrderedDict

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics, viewsets, pagination, exceptions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import ItemForm
from .models import Attribute, Category, Item
from .serializers import (
    CategorySerializer,
    CategoryLSerializer,
    CategoryRFieldAttributeSerializer,
    CategoryRFilterAttributeSerializer,
    ImageSerializer,
    ItemLSerializer,
    ItemLPromotionSerializer,
    ItemRSerializer,
    ItemPSerializer,
)

from locations.serializers import LocationOptionSerializer

from direct.models import Participant

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


def search(request):
    try:
        page = request.GET.get("page", 1)
    except PageNotAnInteger:
        page = 1

    items = Item.objects.all()[:10]

    p = Paginator(items, request=request, per_page=3)

    paginated_items = p.page(page)

    return render(request, "classifieds/search.html", {"items": paginated_items})


def detail(request, id):
    item = get_object_or_404(Item, id=id)

    related_items = Item.objects.filter_by_related(item)

    return render(
        request,
        "classifieds/detail.html",
        {"item": item, "related_items": related_items},
    )


def select_category(request):
    l1_categories = Category.objects.filter(level=1)
    l2_categories = Category.objects.filter(level=2)
    return render(
        request,
        "classifieds/select_category.html",
        {"l1_categories": l1_categories, "l2_categories": l2_categories},
    )


def edit(request, id=None):
    category_id = request.GET.get("category_id", None)

    if request.method == "POST":
        form = ItemForm(request.POST, category_id=category_id)
    else:
        form = ItemForm(category_id=category_id)
    return render(request, "classifieds/edit.html", {"form": form})


def api_upload(request):
    data = []
    return JsonResponse(data, safe=False)


class Pagination(pagination.PageNumberPagination):
    page_size = 30

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("total_pages", self.page.paginator.num_pages),
                ]
            )
        )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [
        AllowAny,
    ]

    def get_serializer_class(self):
        if self.action == "root":
            return CategorySerializer
        elif self.action == "retrieve":
            return CategoryRFilterAttributeSerializer
        return CategoryLSerializer

    def get_queryset(self):
        if self.action == "list":
            level = self.request.query_params.get("level", 1)
            return self.queryset.prefetch_related("children").filter(level=level)
        elif self.action == "root":
            return self.queryset
        elif self.action == "retrieve":
            return self.queryset.select_related("parent").prefetch_related("children")
        return self.queryset

    @action(["get"], detail=False)
    def root(self, request, *args, **kwargs):
        queryset = self.queryset.filter(level=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def set(self, request, *args, **kwargs):
        data = {
            "selected": None,
            "l1_value": "",
            "l2_value": "",
            "l1_options": [],
            "l2_options": [],
            "sorts": [],
        }
        selected_id = self.request.query_params.get("selected_id", None)
        categories = Category.objects.select_related("parent").prefetch_related(
            "children"
        )

        sorts = [
            {"value": "", "name": "新しい順"},
            {"value": "recommended", "name": "おすすめ順"},
        ]

        l1_categories = categories.filter(level=1)
        data["l1_options"] = CategorySerializer(l1_categories, many=True).data

        if selected_id:
            selected_category = get_object_or_404(
                categories.prefetch_related("filter_attributes"), id=selected_id
            )

            for attribute in selected_category.filter_attributes.all():
                if attribute.filter_type == Attribute.FilterType.RANGE_INPUT:
                    sorts.append(
                        {
                            "value": "%s_asc" % attribute.slug,
                            "name": "%sが低い順" % attribute.name,
                        }
                    )
                    sorts.append(
                        {
                            "value": "%s_desc" % attribute.slug,
                            "name": "%sが高い順" % attribute.name,
                        }
                    )

            if selected_category.level == 1:
                l2_categories = selected_category.children.all()
                data["selected"] = CategoryRFilterAttributeSerializer(
                    selected_category
                ).data
                data["l1_value"] = int(selected_id)
                data["l2_options"] = CategorySerializer(l2_categories, many=True).data
            elif selected_category.level == 2:
                l2_categories = selected_category.parent.children.all()
                data["selected"] = CategoryRFilterAttributeSerializer(
                    selected_category
                ).data
                data["l1_value"] = selected_category.parent_id
                data["l2_value"] = int(selected_id)
                data["l2_options"] = CategorySerializer(l2_categories, many=True).data

        data["sorts"] = sorts

        return Response(data)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    pagination_class = Pagination

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "fixed":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "retrieve":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "related":
            self.permission_classes = [
                AllowAny,
            ]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "list":
            return (
                self.queryset.select_related("category", "location")
                .prefetch_related("image_set", "promotion_set")
                .filter_by_query(self.request.query_params)
                .filter_by_unfixed()
            )
        elif self.action == "fixed":
            return (
                self.queryset.prefetch_related("promotion_set__type")
                .filter_by_query(self.request.query_params)
                .filter_by_fixed()
            )
        elif self.action == "retrieve":
            return self.queryset.select_related(
                "author", "category__parent", "location"
            ).prefetch_related(
                "image_set",
                "category__children",
                "category__field_attributes__option_set",
            )
        elif self.action == "related":
            return self.queryset.select_related("category", "location")
        elif self.action == "form_data":
            return self.queryset.select_related(
                "category",
                "location__parent",
                "author",
            ).prefetch_related(
                "category__field_attributes__option_set",
                "category__promotions__option_set",
                "promotion_set__type",
            )
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ItemLPromotionSerializer
        elif self.action == "fixed":
            return ItemLPromotionSerializer
        elif self.action == "retrieve":
            return ItemRSerializer
        elif self.action == "empty_form_data":
            return ItemPSerializer
        elif self.action == "form_data":
            return ItemPSerializer
        elif self.action == "create":
            return ItemPSerializer
        elif self.action == "update":
            return ItemPSerializer
        return ItemLSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        item = serializer.save()
        context = {
            "item": item,
            "protocol": self.request.scheme,
            "domain": get_current_site(self.request).domain,
        }
        subject = "投稿が完了しました"
        message = render_to_string("email/post_completed_message.txt", context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [item.author.email])

    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())

    @action(["post"], detail=True)
    def renew(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.updated_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_200_OK)

    @action(["get"], detail=False)
    def fixed(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["get"], detail=True)
    def related(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = (
            Item.objects.select_related(
                "category",
                "location",
            )
            .prefetch_related(
                "image_set",
            )
            .filter_by_related(instance)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["get"], detail=True, url_path="get-existing-participant")
    def get_existing_participant(self, request, *args, **kwargs):
        instance = self.get_object()
        participant_id = None
        try:
            participant = Participant.objects.get(
                thread__item=instance, user=self.request.user
            )
        except Participant.DoesNotExist:
            participant = None
        if participant:
            participant_id = participant.id
        return Response(participant_id)

    def add_default_value_to_attribute(self, data, attribute):
        if attribute.slug == "rent_type":
            data["attributes"][attribute.slug] = 1
        elif attribute.field_type == Attribute.FieldType.BOOLEAN:
            data["attributes"][attribute.slug] = False
        elif attribute.field_type == Attribute.FieldType.MULTIPLE_CHECKBOX:
            data["attributes"][attribute.slug] = []
        else:
            data["attributes"][attribute.slug] = ""

    def add_default_value_to_promotions(self, data, promotions):
        data["promotions"] = {"types": {}, "options": {}}
        for promotion in promotions:
            data["promotions"]["types"][promotion.slug] = False
            data["promotions"]["options"][promotion.slug] = str(
                promotion.option_set.first().id
            )

    @action(["get"], detail=False, url_path="empty-form-data")
    def empty_form_data(self, request, *args, **kwargs):
        data = self.get_serializer().data

        category_id = self.request.query_params.get("category_id")
        if category_id:
            category = get_object_or_404(
                Category.objects.select_related("parent").prefetch_related(
                    "field_attributes__option_set", "promotions__option_set"
                ),
                id=category_id,
            )

            data["category"] = category_id
            data["category_object"] = CategoryRFieldAttributeSerializer(category).data
            data["attributes"] = {}

            for attribute in category.field_attributes.all():
                self.add_default_value_to_attribute(data, attribute)

        data["location"] = None

        data["active_promotions"] = {}
        self.add_default_value_to_promotions(data, category.promotions.all())
        return Response(data)

    @action(["get"], detail=True, url_path="form-data")
    def form_data(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.author != self.request.user:
            raise exceptions.PermissionDenied()

        data = self.get_serializer(instance).data

        for key in data:
            if key != "attributes":
                if not data[key]:
                    data[key] = ""

        for attribute in instance.category.field_attributes.all():
            if attribute.slug not in instance.attributes.keys():
                self.add_default_value_to_attribute(data, attribute)
            else:
                if attribute.field_type == Attribute.FieldType.DECIMAL:
                    if not data["attributes"][attribute.slug]:
                        data["attributes"][attribute.slug] = ""

        data["location"] = LocationOptionSerializer(instance.location).data

        data["active_promotions"] = {}
        for promotion in instance.promotion_set.all():
            data["active_promotions"][promotion.type.slug] = promotion.disabled_at
        self.add_default_value_to_promotions(data, instance.category.promotions.all())
        return Response(data)


class ImageCreateView(generics.CreateAPIView):
    serializer_class = ImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]
