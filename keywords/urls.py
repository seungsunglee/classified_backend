from django.urls import path

from . import views

from rest_framework.routers import DefaultRouter

app_name = "keywords"
urlpatterns = []

router = DefaultRouter()
router.register("", views.KeywordViewSet)

urlpatterns += router.urls
