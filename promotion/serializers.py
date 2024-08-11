from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from .models import Type, Option, PaymentHistory


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ("id", "term", "price")


class OptionLSerializer(OptionSerializer):
    pass


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = (
            "slug",
            "name",
            "description",
        )


class TypeLSerializer(TypeSerializer):
    pass


class TypeRSerializer(TypeSerializer):
    options = serializers.SerializerMethodField()

    class Meta(TypeSerializer.Meta):
        fields = TypeSerializer.Meta.fields + ("options",)

    def get_options(self, obj):
        options = []
        for option in obj.option_set.all():
            options.append(OptionLSerializer(option).data)
        return options


class OptionRSerializer(OptionSerializer):
    type = TypeLSerializer()

    class Meta(OptionSerializer.Meta):
        fields = OptionSerializer.Meta.fields + ("type",)


class PaymentHistorySerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    options = OptionRSerializer(many=True)

    class Meta:
        model = PaymentHistory
        fields = (
            "id",
            "item",
            "options",
            "total_price",
            "created_at",
        )

    def get_item(self, obj):
        if obj.item:
            return obj.item.title
        return "削除された投稿"
