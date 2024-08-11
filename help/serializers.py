from django.contrib.humanize.templatetags.humanize import intcomma, intword
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from .models import Topic, Article


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = (
            "id",
            "title",
        )


class TopicLSerializer(TopicSerializer):
    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields


class TopicRSerializer(TopicSerializer):
    parents = serializers.SerializerMethodField()

    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields + ("parents",)

    def get_parents(self, obj):
        parents = []
        current_topic_parent = obj.parent
        while current_topic_parent is not None:
            parents.append(TopicSerializer(current_topic_parent).data)
            current_topic_parent = current_topic_parent.parent
        return parents


class TopicRChildrenSerializer(TopicRSerializer):
    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields


class ArticleSerializer(serializers.ModelSerializer):
    topic = TopicSerializer

    class Meta:
        model = Article
        fields = (
            "id",
            "topic",
            "title",
            "content",
        )
