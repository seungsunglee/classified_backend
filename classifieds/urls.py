from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views


urlpatterns = [
    path("search/", views.search, name='search'),
    path("p/<int:id>/", views.detail, name='detail'),
    path("select-category/", views.select_category, name='select_category'),
    path("new/", views.edit, name='new'),
    path("edit/<int:id>/", views.edit, name='edit'),
    path("images/", views.ImageCreateView.as_view()),
]

router = DefaultRouter()
router.register("categories", views.CategoryViewSet)
router.register("items", views.ItemViewSet)

urlpatterns += router.urls
