from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics, serializers, status, viewsets, pagination
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    TopicSerializer,
    TopicLSerializer,
    TopicRSerializer,
    TopicRChildrenSerializer,
    ArticleSerializer,
)

from .models import Topic, Article


def detail(request, id):
    article = get_object_or_404(Article, id=id)
    return render(request, 'help/detail.html', {
        'article': article
    })


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicLSerializer
    permission_classes = [
        AllowAny,
    ]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TopicRSerializer(instance)
        return Response(serializer.data)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [
        AllowAny,
    ]
