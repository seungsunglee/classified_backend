from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Location
from .serializers import (
    LocationSerializer,
    LocationLSerializer,
    LocationRSerializer,
    LocationOptionSerializer,
)

from classifieds.models import Item


def api_autocomplete(request):
    data = []
    term = request.GET.get("term", None)
    if term:
        locations = Location.objects.filter(level=2).filter(
            name_with_postcode__icontains=term
        )[:30]
        for location in locations:
            data.append(
                {"id": location.id, "value": location.name_with_postcode_and_state}
            )
    return JsonResponse(data, safe=False)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    permission_classes = [
        AllowAny,
    ]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LocationRSerializer
        elif self.action == "autocomplete":
            return LocationOptionSerializer
        return LocationLSerializer

    def get_queryset(self):
        if self.action == "list":
            query_params = self.request.query_params
            term = query_params.get("term")
            if term:
                return self.queryset.filter(level=3).filter(
                    address_name__icontains=term
                )[:10]
            else:
                level = query_params.get("level", 1)
                self.queryset = self.queryset.filter(level=level)
        return self.queryset

    @action(["get"], detail=False)
    def autocomplete(self, request, *args, **kwargs):
        queryset = self.queryset
        term = self.request.query_params.get("term")
        queryset = queryset.filter(level=2).filter(name_with_postcode__icontains=term)[
            :30
        ]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def root(self, request, *args, **kwargs):
        queryset = self.queryset.filter(level=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def popular(self, request, *args, **kwargs):
        queryset = self.queryset.filter(id__in=[16002, 16004, 16007, 16008])
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
        }
        selected_id = self.request.query_params.get("selected_id", None)
        locations = Location.objects.select_related("parent").prefetch_related(
            "parent__children"
        )

        l1_locations = locations.filter(level=1)
        data["l1_options"] = LocationSerializer(l1_locations, many=True).data

        if selected_id:
            selected_location = get_object_or_404(locations, id=selected_id)
            if selected_location.level == 1:
                l2_locations = selected_location.children.filter(
                    item__isnull=False
                ).distinct()
                data["selected"] = LocationSerializer(selected_location).data
                data["l1_value"] = int(selected_id)
                data["l2_options"] = LocationOptionSerializer(
                    l2_locations, many=True
                ).data
            elif selected_location.level == 2:
                l2_locations = selected_location.parent.children.filter(
                    item__isnull=False
                ).distinct()
                data["selected"] = LocationSerializer(selected_location).data
                data["l1_value"] = selected_location.parent_id
                data["l2_value"] = int(selected_id)
                data["l2_options"] = LocationOptionSerializer(
                    l2_locations, many=True
                ).data

        return Response(data)
