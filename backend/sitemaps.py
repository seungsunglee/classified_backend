from django.contrib.sitemaps import Sitemap

from classifieds.models import Category, Item
from locations.models import Location
from keywords.models import Keyword


class Category1DepthSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Category.objects.filter(level=1).order_by("id")

    def location(self, obj):
        return "/classifieds/search?category_id=%s" % obj.id


class Category2DepthSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    limit = 5000

    def items(self):
        return Category.objects.filter(item__isnull=False).distinct()

    def location(self, obj):
        return "/classifieds/search?category_id=%s" % obj.id


class Location1DepthSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Location.objects.filter(level=1).order_by("id")

    def location(self, obj):
        return "/classifieds/search?location_id=%s" % obj.id


class Location2DepthSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    limit = 5000

    def items(self):
        return Location.objects.filter(item__isnull=False).distinct()

    def location(self, obj):
        return "/classifieds/search?location_id=%s" % obj.id


class ItemSitemap(Sitemap):
    changefreq = "monthly"
    priority = 1.0
    limit = 5000

    def items(self):
        return Item.objects.all()

    def location(self, obj):
        return "/classifieds/p/%s" % obj.id

    def lastmod(self, obj):
        return obj.updated_at.date()


class KeywordSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Keyword.objects.filter(confirmed=True).order_by("id")

    def location(self, obj):
        return "/classifieds/search?keyword=%s" % obj.title


sitemaps = {
    "category-1depth": Category1DepthSitemap,
    "category-2depth": Category2DepthSitemap,
    "location-1depth": Location1DepthSitemap,
    "location-2depth": Location2DepthSitemap,
    "item": ItemSitemap,
    "keyword": KeywordSitemap,
}
