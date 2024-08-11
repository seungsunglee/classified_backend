from collections import OrderedDict

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView

from rest_framework import generics, status, views, viewsets, pagination, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .forms import SignupForm, SetPasswordForm
from .models import Bookmark, Block
from .serializers import (
    BookmarkSerializer,
    AuthUserSerializer,
    UserCreateSerializer,
    LoginSerializer,
    ActivationSerializer,
    SendEmailResetSerializer,
    PasswordResetConfirmRetypeSerializer,
    SetPasswordSerializer,
)
from .utils import encode_uid

from classifieds.models import Item
from classifieds.serializers import ManageItemLSerializer

from promotion.models import PaymentHistory
from promotion.serializers import PaymentHistorySerializer

User = get_user_model()


class LoginView(DjangoLoginView):
    template_name = 'authentication/login.html'


class LogoutView(DjangoLogoutView):
    pass


class SignupView(CreateView):
    template_name = 'authentication/signup.html'
    form_class = SignupForm


class PasswordResetView(DjangoPasswordResetView):
    template_name = 'authentication/password_reset_form.html'
    email_template_name = 'email/password_reset_email.txt'
    subject_template_name = 'email/password_reset_subject.txt'
    success_url = reverse_lazy('authentication:password_reset_done')


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'authentication/password_reset_done.html'


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('authentication:password_reset_complete')


class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'authentication/password_reset_complete.html'


class Pagination(pagination.LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("offset", self.offset + self.limit),
                    ("results", data),
                ]
            )
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "activation":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "resend_activation":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "reset_password":
            self.permission_classes = [
                AllowAny,
            ]
        elif self.action == "reset_password_confirm":
            self.permission_classes = [
                AllowAny,
            ]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        elif self.action == "activation":
            return ActivationSerializer
        elif self.action == "resend_activation":
            return SendEmailResetSerializer
        elif self.action == "set_password":
            return SetPasswordSerializer
        elif self.action == "reset_password":
            return SendEmailResetSerializer
        elif self.action == "reset_password_confirm":
            return PasswordResetConfirmRetypeSerializer
        return AuthUserSerializer

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        login(self.request, user)

        context = {
            "user": user,
            "protocol": self.request.scheme,
            "domain": get_current_site(self.request).domain,
            "uid": encode_uid(user.pk),
            "token": default_token_generator.make_token(user),
        }
        message = render_to_string("email/activation_message.txt", context)
        send_mail(
            "メールアドレスを認証してください", message, settings.DEFAULT_FROM_EMAIL, [user.email]
        )

        return Response(
            data=AuthUserSerializer(user).data, status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        old_user = self.get_instance()
        new_email = serializer.validated_data.get("email")

        if old_user.email != new_email:
            context = {
                "user": old_user,
                "protocol": self.request.scheme,
                "domain": get_current_site(self.request).domain,
                "uid": encode_uid(old_user.pk),
                "token": default_token_generator.make_token(old_user),
            }
            message = render_to_string("email/activation_message.txt", context)
            send_mail(
                "メールアドレスを認証してください", message, settings.DEFAULT_FROM_EMAIL, [new_email]
            )
            serializer.save(email_confirmed=False)
        else:
            serializer.save()

        serializer.save()

    @action(["get", "put", "patch", "delete"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy(request, *args, **kwargs)

    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.email_confirmed = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="resend-activation")
    def resend_activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        context = {
            "user": user,
            "protocol": self.request.scheme,
            "domain": get_current_site(self.request).domain,
            "uid": encode_uid(user.pk),
            "token": default_token_generator.make_token(user),
        }
        message = render_to_string("email/activation_message.txt", context)
        send_mail(
            "メールアドレスを認証してください", message, settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="set-password")
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        update_session_auth_hash(self.request, self.request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="reset-password")
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        if user:
            context = {
                "user": user,
                "protocol": self.request.scheme,
                "domain": get_current_site(self.request).domain,
                "uid": encode_uid(user.pk),
                "token": default_token_generator.make_token(user),
            }
            message = render_to_string("email/password_reset_message.txt", context)
            send_mail("パスワードの再設定", message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="reset-password-confirm")
    def reset_password_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.user.set_password(serializer.data["new_password"])
        if hasattr(serializer.user, "last_login"):
            serializer.user.last_login = timezone.now()
        serializer.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="confirm-direct")
    def confirm_direct(self, request, *args, **kwargs):
        user = self.get_instance()
        user.direct_confirmed_at = timezone.now()
        user.save()
        return Response(status=status.HTTP_200_OK)


'''
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login(self.request, serializer.user)
        return Response(
            data=AuthUserSerializer(serializer.user).data, status=status.HTTP_200_OK
        )


class LogoutView(views.APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
'''


class UserItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ManageItemLSerializer
    pagination_class = Pagination

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.prefetch_related(
                "image_set", "bookmark_set", "promotion_set__type"
            ).filter(author=self.request.user)
        return super().get_queryset()


class UserBookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()
    pagination_class = Pagination
    lookup_field = "item"

    def list(self, request, *args, **kwargs):
        data = self.queryset.filter(user=self.request.user).values_list(
            "item", flat=True
        )
        return Response(data)

    @action(["post"], detail=True)
    def bookmark(self, request, *args, **kwargs):
        bookmarked = False
        _, created = Bookmark.objects.get_or_create(
            user=self.request.user, item_id=self.kwargs["item"]
        )
        if created:
            bookmarked = True
        return Response({"bookmarked": bookmarked})

    @action(["post"], detail=True)
    def unbookmark(self, request, *args, **kwargs):
        unbookmarked = False
        try:
            bookmark = Bookmark.objects.get(
                user=self.request.user, item_id=self.kwargs["item"]
            )
            bookmark.delete()
            unbookmarked = True
        except Bookmark.DoesNotExist:
            pass
        return Response({"unbookmarked": unbookmarked})

    @action(["get"], detail=False)
    def items(self, request, *args, **kwargs):
        queryset = (
            self.queryset.select_related("item")
            .prefetch_related(
                "item__category",
                "item__location",
                "item__image_set",
            )
            .filter(user=self.request.user)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserBlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    lookup_field = "target"

    def list(self, request, *args, **kwargs):
        data = self.queryset.filter(user=self.request.user).values_list(
            "target", flat=True
        )
        return Response(data)

    @action(["post"], detail=True)
    def block(self, request, *args, **kwargs):
        blocked = False
        _, created = Block.objects.get_or_create(
            user=self.request.user, target_id=self.kwargs["target"]
        )
        if created:
            blocked = True
        return Response({"blocked": blocked})

    @action(["post"], detail=True)
    def unblock(self, request, *args, **kwargs):
        unblocked = False
        try:
            block = Block.objects.get(
                user=self.request.user, target_id=self.kwargs["target"]
            )
            block.delete()
            unblocked = True
        except Bookmark.DoesNotExist:
            pass
        return Response({"unblocked": unblocked})

    @action(["get"], detail=True, url_path="is-blocked")
    def is_blocked(self, request, *args, **kwargs):
        return Response(
            {
                "is_blocked": Block.objects.filter(user_id=self.kwargs["target"])
                .filter(target=self.request.user)
                .exists()
            }
        )


class UserPaymentHistoyViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentHistorySerializer
    queryset = PaymentHistory.objects.all()
    pagination_class = Pagination

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("item")
            .prefetch_related("options__type")
            .filter(user=self.request.user)
        )
