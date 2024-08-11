from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    path('article/<int:id>/', views.detail, name='detail'),
]

router = DefaultRouter()
router.register("topics", views.TopicViewSet)
router.register("articles", views.ArticleViewSet)

urlpatterns += router.urls
