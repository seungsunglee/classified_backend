from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.urls import path, include
from django.views.generic import TemplateView

from .sitemaps import sitemaps

from classifieds import views as classifieds_views
from locations import views as locations_views

urlpatterns = [
    path("", include(("home.urls", "home"))),
    path("", include(("authentication.urls", "authentication"))),
    path("account/", include(("accounts.urls", "accounts"))),
    path("classifieds/", include(("classifieds.urls", "classifieds"))),
    path("help/", include(("help.urls", "help"))),
    path(
        "api/",
        include(
            [
                path("classifieds/upload/", classifieds_views.api_upload),
                path("locations/autocomplete/", locations_views.api_autocomplete),
            ]
        ),
    ),
    path("markdownx/", include("markdownx.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sitemap.xml",
        sitemaps_views.index,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.index",
    ),
    path(
        "sitemap-<section>.xml",
        sitemaps_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "ads.txt",
        TemplateView.as_view(template_name="ads.txt", content_type="text/plain"),
    ),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns


"""
    path(
        "api/v1/",
        include(
            [
                path("accounts/", include("accounts.urls")),
                path("auth/", include("authentication.urls")),
                path("classifieds/", include("classifieds.urls")),
                path("locations/", include("locations.urls")),
                path("keywords/", include("keywords.urls")),
                path("direct/", include("direct.urls")),
                path("promotion/", include("promotion.urls")),
                path("help/", include("help.urls")),
            ]
        ),
    ),
    """
