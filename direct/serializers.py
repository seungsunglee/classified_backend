from rest_framework import serializers

from .models import Participant, Thread, Response

from authentication.models import User, Image
from classifieds.serializers import ItemLSerializer


class PublicUserSerializerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("file",)


class PublicUserSerializer(serializers.ModelSerializer):
    image = PublicUserSerializerImageSerializer()

    class Meta:
        model = User
        fields = ("id", "username", "image")


class LastResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ("id", "content")


class ResponseLSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer()

    class Meta:
        model = Response
        fields = (
            "id",
            "thread",
            "sender",
            "content",
            "created_at",
        )


class ResponsePSerializer(serializers.ModelSerializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Response
        fields = (
            "id",
            "thread",
            "sender",
            "receiver",
            "content",
        )


class ThreadSerializer(serializers.ModelSerializer):
    item = ItemLSerializer()

    class Meta:
        model = Thread
        fields = (
            "id",
            "item",
        )


class ParticipantSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer()
    opponent = PublicUserSerializer()

    class Meta:
        model = Participant
        fields = (
            "id",
            "thread",
            "user",
            "opponent",
        )


class ParticipantLSerializer(ParticipantSerializer):
    last_response = LastResponseSerializer()

    class Meta(ParticipantSerializer.Meta):
        fields = ParticipantSerializer.Meta.fields + (
            "last_response",
            "is_read",
        )


class ParticipantRSerializer(ParticipantSerializer):
    pass
