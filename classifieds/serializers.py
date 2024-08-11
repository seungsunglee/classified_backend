from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from .models import Option, Attribute, Category, Item, Promotion, Image

from authentication.models import User, Image as AuthImage

from locations.serializers import LocationLSerializer

from promotion.serializers import TypeRSerializer, TypeLSerializer


class AuthorImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthImage
        fields = ("file",)


class AuthorSerializer(serializers.ModelSerializer):
    image = AuthorImageSerializer()
    items = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "image",
            "items",
        )

    def get_items(self, obj):
        return obj.item_set.count()


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = (
            "name",
            "value",
        )


class FieldAttributeSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = (
            "name",
            "slug",
            "field_type",
            "options",
        )

    def get_options(self, obj):
        options = []
        if (
            obj.field_type == Attribute.FieldType.OPTION
            or obj.field_type == Attribute.FieldType.MULTIPLE_CHECKBOX
            or obj.field_type == Attribute.FieldType.RADIO
        ):
            for option in obj.option_set.all():
                options.append(OptionSerializer(option).data)
        return options


class FilterAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = (
            "name",
            "slug",
            "filter_type",
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "title",
            "level",
            "parent",
        )


class CategoryLSerializer(CategorySerializer):
    children = CategorySerializer(many=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ("children",)


class CategoryRSerializer(CategoryLSerializer):
    parent = CategorySerializer()


class CategoryRFieldAttributeSerializer(CategoryRSerializer):
    field_attributes = FieldAttributeSerializer(many=True)
    promotions = TypeRSerializer(many=True)

    class Meta(CategoryRSerializer.Meta):
        fields = CategoryRSerializer.Meta.fields + (
            "field_attributes",
            "promotions",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["field_attributes"] = {
            attribute["slug"]: attribute for attribute in ret["field_attributes"]
        }
        return ret


class CategoryRFilterAttributeSerializer(CategoryRSerializer):
    filter_attributes = FilterAttributeSerializer(many=True)

    class Meta(CategoryRSerializer.Meta):
        fields = CategoryRSerializer.Meta.fields + ("filter_attributes",)


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = (
            "id",
            "file",
            "temp_id",
        )


class AttributeMixin:
    def get_formatted_price(self, value, no_price=False):
        if not no_price:
            return "$%s" % intcomma(value)
        else:
            return "無料"

    def get_formatted_rent(self, value):
        return "$%s" % intcomma(value)

    def get_price(self, obj):
        if "rent" in obj.attributes:
            return self.get_formatted_rent(obj.attributes["rent"])
        elif "price" in obj.attributes:
            return self.get_formatted_price(
                obj.attributes["price"], obj.attributes["no_price"]
            )
        else:
            return None

    def get_attributes(self, obj):
        attributes = []
        return attributes


class ItemLSerializer(AttributeMixin, serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = (
            "id",
            "title",
            "description",
            "category",
            "location",
            "price",
            "image",
            "updated_at",
        )

    def get_category(self, obj):
        if obj.category:
            return obj.category.name
        else:
            return ""

    def get_location(self, obj):
        return "%s, %s" % (obj.location.name, obj.location.state_code)

    def get_image(self, obj):
        image_set = obj.image_set.all()
        if image_set.exists():
            return image_set.first().file.url
        return None


class ItemLPromotionSerializer(ItemLSerializer):
    promotions = serializers.SerializerMethodField()

    class Meta(ItemLSerializer.Meta):
        fields = ItemLSerializer.Meta.fields + ("promotions",)

    def get_promotions(self, obj):
        promotions = []
        for promotion in obj.promotion_set.all():
            promotions.append(promotion.type.slug)
        return promotions


class ManageItemLSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    bookmarks = serializers.SerializerMethodField()
    promotions = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = (
            "id",
            "title",
            "image",
            "updated_at",
            "views",
            "bookmarks",
            "promotions",
        )

    def get_bookmarks(self, obj):
        return obj.bookmark_set.count()

    def get_promotions(self, obj):
        promotions = []
        for promotion in obj.promotion_set.all():
            promotions.append(promotion.type.slug)
        return promotions

    def get_image(self, obj):
        image_set = obj.image_set.all()
        if image_set.exists():
            return image_set.first().file.url
        return None


class PromotionSerializer(serializers.ModelSerializer):
    type = TypeLSerializer()

    class Meta:
        model = Promotion
        fields = ("type", "disabled_at")


class ItemRSerializer(AttributeMixin, serializers.ModelSerializer):
    author = AuthorSerializer()
    category = CategoryRSerializer()
    location = LocationLSerializer()
    price = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    images = ImageSerializer(source="image_set", many=True)

    class Meta:
        model = Item
        fields = (
            "id",
            "author",
            "title",
            "description",
            "category",
            "location",
            "price",
            "attributes",
            "images",
            "created_at",
            "updated_at",
        )


class SaveImageMixin:
    def save_image(self, instance):
        request_data = self.context.get("request").data

        deleted_images = request_data.get("deleted_images")
        if deleted_images and len(deleted_images) > 0:
            for deleted_image in deleted_images:
                try:
                    image = Image.objects.get(id=deleted_image)
                except Image.DoesNotExist:
                    pass
                else:
                    image.delete()

        images = request_data.get("images")
        if images and len(images) > 0:
            image_index = 1
            for image in images:
                try:
                    image = Image.objects.get(id=image["id"])
                except Image.DoesNotExist:
                    pass
                else:
                    image.item = instance
                    image.index = image_index
                    image.save()
                    image_index += 1


class ItemPSerializer(SaveImageMixin, serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category_object = serializers.SerializerMethodField()
    images = ImageSerializer(source="image_set", many=True, read_only=True)

    class Meta:
        model = Item
        fields = (
            "id",
            "author",
            "category",
            "category_object",
            "title",
            "description",
            "attributes",
            "location",
            "images",
        )

    def get_category_object(self, obj):
        return CategoryRFieldAttributeSerializer(obj.category).data

    def modify_attributes_value(self, attributes):
        if "no_price" in attributes and attributes["no_price"]:
            attributes["price"] = None

    def create(self, validated_data):
        self.modify_attributes_value(validated_data["attributes"])

        item = Item.objects.create(**validated_data)
        self.save_image(item)
        return item

    def update(self, instance, validated_data):
        attributes = validated_data["attributes"]

        category_attributes_slug_list = instance.category.field_attributes.values_list(
            "slug", flat=True
        )

        for key in list(attributes):
            if key not in category_attributes_slug_list:
                attributes.pop(key)

        self.modify_attributes_value(attributes)

        super().update(instance, validated_data)
        self.save_image(instance)
        return instance
