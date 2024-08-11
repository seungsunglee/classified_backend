from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Keyword
from .serializers import KeywordSerializer

import pykakasi


class KeywordViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = [
        AllowAny,
    ]

    @action(["get"], detail=False)
    def autocomplete(self, request, *args, **kwargs):
        queryset = self.queryset
        term = self.request.query_params.get("term")

        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")
        kakasi.setMode("K", "a")
        kakasi.setMode("J", "a")
        conversion = kakasi.getConverter()
        converted_term = conversion.do(term)

        queryset = queryset.filter(confirmed=True).filter(
            roman_alphabet__istartswith=converted_term
        )[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(["post"], detail=False)
    def register(self, request, *args, **kwargs):
        keyword = self.request.data["keyword"]
        if keyword:
            title = " ".join(keyword.strip().split())

            kakasi = pykakasi.kakasi()
            kakasi.setMode("H", "a")
            kakasi.setMode("K", "a")
            kakasi.setMode("J", "a")
            conversion = kakasi.getConverter()
            roman_alphabet = conversion.do(title)

            if not Keyword.objects.filter(
                title=title, roman_alphabet=roman_alphabet
            ).exists():
                Keyword.objects.create(title=title, roman_alphabet=roman_alphabet)

        return Response(status=status.HTTP_204_NO_CONTENT)
