from django.contrib import admin

from .models import Topic, Article

from markdownx.admin import MarkdownxModelAdmin


class ArticleAdmin(MarkdownxModelAdmin):
    list_display = (
        "title",
        "topic",
    )


admin.site.register(Topic)
admin.site.register(Article, ArticleAdmin)
