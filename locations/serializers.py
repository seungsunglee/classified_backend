from rest_framework import serializers

from .models import Location


class LocationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "name_with_postcode",
            "name_with_postcode_and_state",
        )


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "name",
            "name_with_postcode_and_state",
            "state_code",
            "state",
            "parent",
            "level",
        )


class LocationLSerializer(LocationSerializer):
    pass


class LocationRSerializer(LocationSerializer):
    children = serializers.SerializerMethodField()

    class Meta(LocationSerializer.Meta):
        fields = LocationSerializer.Meta.fields + ("children",)

    def get_children(self, obj):
        children = Location.objects.filter(parent=obj)
        return LocationSerializer(children, many=True).data
