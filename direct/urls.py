from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = []

router = DefaultRouter()
router.register("participants", views.ParticipantViewSet)
router.register("responses", views.ResponseViewSet)

urlpatterns += router.urls
