from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError

from .models import Image, Bookmark
from .utils import decode_uid

from classifieds.serializers import ItemLSerializer

User = get_user_model()


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("file",)


class BookmarkSerializer(serializers.ModelSerializer):
    item = ItemLSerializer()

    class Meta:
        model = Bookmark
        fields = ("item",)


class PublicUserSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    items = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email_confirmed",
            "introduction",
            "website",
            "image",
            "date_joined",
            "items",
        )

    def get_items(self, obj):
        return obj.item_set.count()


class AuthUserSerializer(serializers.ModelSerializer):
    image = ImageSerializer(required=False, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "email_confirmed",
            "introduction",
            "website",
            "image",
            "date_joined",
        )

    def save_image(self, instance):
        request = self.context.get("request")
        file = request.FILES.get("file")

        if file:
            if hasattr(instance, "image"):
                instance.image.file.delete()
                instance.image.file = file
                instance.image.save()
            else:
                Image.objects.create(user=instance, file=file)
        else:
            if hasattr(instance, "image") and request.POST.get("deleted_image"):
                instance.image.file.delete()

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        self.save_image(instance)
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    default_error_messages = {
        "cannot_create_user": _("アカウントを作成できません。"),
    }

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
        )

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )
        return attrs

    def create(self, validated_data):
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")

        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            user.is_active = True
            user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True
    )

    default_error_messages = {
        "invalid_login": _("正しいメールアドレスとパスワードを入力してください。"),
        "inactive": _("このアカウントは使用できません。"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        self.user = authenticate(
            request=self.context.get("request"), username=username, password=password
        )
        if not self.user:
            self.fail("invalid_login")
        else:
            if not self.user.is_active:
                self.fail("inactive")
            else:
                return self.user


class UidAndTokenSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False)
    token = serializers.CharField(required=False)

    default_error_messages = {
        "invalid_uid_token": _("認証リンクの有効期限が過ぎたか、すでに使用された可能性があります。"),
    }

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        try:
            uid = decode_uid(self.initial_data.get("uid", ""))
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            self.fail("invalid_uid_token")

        is_token_valid = default_token_generator.check_token(
            self.user, self.initial_data.get("token", "")
        )
        if is_token_valid:
            return validated_data
        else:
            self.fail("invalid_uid_token")


class ActivationSerializer(UidAndTokenSerializer):
    default_error_messages = {"stale_token": _("認証リンクの有効期限が切れています。")}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.user.email_confirmed:
            return attrs
        raise exceptions.PermissionDenied(self.error_messages["stale_token"])


class UserFunctionsMixin:
    def get_user(self, is_active=True):
        try:
            user = User._default_manager.get(
                is_active=is_active,
                **{"email": self.data.get("email", "")},
            )
            if user.has_usable_password():
                return user
        except User.DoesNotExist:
            pass


class SendEmailResetSerializer(serializers.Serializer, UserFunctionsMixin):
    email = serializers.EmailField()


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        user = self.context["request"].user or self.user
        assert user is not None

        try:
            validate_password(attrs["new_password"], user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return super().validate(attrs)


class PasswordRetypeSerializer(PasswordSerializer):
    re_new_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = {"password_mismatch": _("パスワードが一致しません。")}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["new_password"] == attrs["re_new_password"]:
            return attrs
        else:
            self.fail("password_mismatch")


class CurrentPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = {"invalid_password": _("パスワードを正しく入力してください。")}

    def validate_current_password(self, value):
        is_password_valid = self.context["request"].user.check_password(value)
        if is_password_valid:
            return value
        else:
            self.fail("invalid_password")


class PasswordResetConfirmRetypeSerializer(
    UidAndTokenSerializer, PasswordRetypeSerializer
):
    pass


class SetPasswordSerializer(PasswordRetypeSerializer, CurrentPasswordSerializer):
    pass
