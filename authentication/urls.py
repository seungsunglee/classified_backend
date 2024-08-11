from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    #path("login/", views.LoginView.as_view()),
    #path("logout/", views.LogoutView.as_view()),
]

'''
router = DefaultRouter()
router.register("user/items", views.UserItemViewSet)
router.register("user/bookmarks", views.UserBookmarkViewSet)
router.register("user/blocks", views.UserBlockViewSet)
router.register("user/payment-history", views.UserPaymentHistoyViewSet)
router.register("user", views.UserViewSet)

urlpatterns += router.urls
'''
