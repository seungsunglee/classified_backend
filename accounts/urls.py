from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

from direct import views as direct_views

urlpatterns = [
    path('profile/<int:id>/', views.manage_items, name='profile'),
    path('manage-items/', views.manage_items, name='manage_items'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('direct/', direct_views.index, name='direct_index'),
    path('direct/<int:id>/', direct_views.detail, name='direct_detail'),
    path('payment-history/', views.manage_items, name='payment_history'),
    path('settings/', views.settings, name='settings'),
    path('security/', views.PasswordChangeView.as_view(), name='security'),
]

router = DefaultRouter()
router.register("users", views.UsersViewSet)

urlpatterns += router.urls
