from collections import OrderedDict

from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.shortcuts import get_object_or_404, render

from django.utils.translation import ugettext_lazy as _

from rest_framework import viewsets, pagination, generics, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .forms import SettingsForm, PasswordChangeForm

from authentication.models import User, Bookmark
from authentication.serializers import PublicUserSerializer

from classifieds.models import Item
from classifieds.serializers import ItemLSerializer

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


def manage_items(request):
    try:
        page = request.GET.get("page", 1)
    except PageNotAnInteger:
        page = 1

    items = Item.objects.filter(author=request.user)

    p = Paginator(items, request=request, per_page=3)

    paginated_items = p.page(page)

    return render(request, 'accounts/manage_items.html', {
        'items': paginated_items
    })


def bookmarks(request):
    try:
        page = request.GET.get("page", 1)
    except PageNotAnInteger:
        page = 1

    bookmarks = Bookmark.objects.filter(user=request.user)

    p = Paginator(bookmarks, request=request, per_page=3)

    paginated_bookmarks = p.page(page)

    return render(request, 'accounts/bookmarks.html', {
        'bookmarks': paginated_bookmarks
    })



def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=request.user)
    else:
        form = SettingsForm(instance=request.user)
    return render(request, 'accounts/settings.html', {
        'form': form
    })


class PasswordChangeView(DjangoPasswordChangeView):
    template_name = 'accounts/security.html'
    form_class = PasswordChangeForm


class Pagination(pagination.LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("offset", self.offset + self.limit),
                    ("results", data),
                ]
            )
        )


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [
        AllowAny,
    ]
    pagination_class = Pagination

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related("image").prefetch_related("item_set")
        elif self.action == "retrieve":
            return self.queryset.select_related("image").prefetch_related("item_set")
        return self.queryset

    def get_serializer_class(self):
        if self.action == "items":
            return ItemLSerializer
        return PublicUserSerializer

    @action(["get"], detail=True)
    def items(self, request, *args, **kwargs):
        queryset = (
            Item.objects.select_related("category", "location")
            .prefetch_related("image_set")
            .filter(author=self.get_object())
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
