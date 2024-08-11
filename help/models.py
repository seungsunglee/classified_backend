from django.db import models

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class Topic(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.title:
            return self.title
        return self.id


class Article(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = MarkdownxField()

    def __str__(self):
        if self.title:
            return self.title
        return self.id

    @property
    def formatted_content(self):
        return markdownify(self.content)
