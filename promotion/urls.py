from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views


urlpatterns = [
    path("items/<int:pk>/", views.ItemRetrieveView.as_view()),
    path("create-checkout-session/", views.CreateCheckoutSessionView.as_view()),
    path("execute/", views.ExecuteView.as_view()),
]

router = DefaultRouter()
router.register("types", views.TypeViewSet)

urlpatterns += router.urls
