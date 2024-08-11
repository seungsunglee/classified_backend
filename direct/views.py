from collections import OrderedDict

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone

from rest_framework import (
    generics,
    serializers,
    status,
    viewsets,
    pagination,
    exceptions,
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Participant, Thread, Response as DirectResponse
from .serializers import (
    ParticipantLSerializer,
    ParticipantRSerializer,
    ResponseLSerializer,
    ResponsePSerializer,
)

from authentication.models import Block

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


def index(request):
    try:
        page = request.GET.get("page", 1)
    except PageNotAnInteger:
        page = 1

    participants = Participant.objects.filter(user=request.user).filter(is_deleted=False).order_by("-updated_at")

    p = Paginator(participants, request=request, per_page=3)

    paginated_participants = p.page(page)

    return render(request, 'accounts/direct/index.html', {
        'participants': paginated_participants
    })


def detail(request, id):
    
    return render(request, 'accounts/direct/detail.html')


class Pagination(pagination.PageNumberPagination):
    page_size = 30

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("total_pages", self.page.paginator.num_pages),
                ]
            )
        )


class ResponsePagination(pagination.PageNumberPagination):
    page_size = 30


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    pagination_class = Pagination

    def get_queryset(self):
        if self.action == "list":
            return (
                self.queryset.select_related(
                    "thread",
                    "thread__item",
                    "thread__item__category",
                    "thread__item__location",
                    "opponent",
                    "opponent__image",
                    "last_response",
                )
                .prefetch_related("thread__item__image_set")
                .filter(user=self.request.user)
                .filter(is_deleted=False)
                .order_by("-updated_at")
            )
        elif self.action == "retrieve":
            return self.queryset.select_related("thread", "user", "opponent")
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == "list":
            return ParticipantLSerializer
        elif self.action == "retrieve":
            return ParticipantRSerializer
        return ParticipantRSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != self.request.user:
            raise exceptions.PermissionDenied()
        if not instance.is_deleted:
            instance.is_read = True
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        blocked = (
            Block.objects.filter(user=self.request.user)
            .filter(target_id=self.request.data["receiver_id"])
            .exists()
        )
        is_blocked = (
            Block.objects.filter(user_id=self.request.data["receiver_id"])
            .filter(target=self.request.user)
            .exists()
        )

        if blocked or is_blocked:
            raise exceptions.ValidationError({"non_field_errors": ["エラーが発生しました。"]})

        try:
            existing_participant_sender = Participant.objects.get(
                thread__item_id=self.request.data["item_id"], user=self.request.user
            )
        except Participant.DoesNotExist:
            existing_participant_sender = None
        if existing_participant_sender:
            raise exceptions.ValidationError({"non_field_errors": ["エラーが発生しました。"]})

        thread = Thread.objects.create(item_id=self.request.data["item_id"])

        response = DirectResponse.objects.create(
            thread=thread,
            sender=self.request.user,
            receiver_id=self.request.data["receiver_id"],
            content=self.request.data["content"],
        )

        participant_sender = Participant.objects.create(
            thread=thread,
            user=self.request.user,
            opponent=response.receiver,
            last_response=response,
            is_read=True,
            deleted_at=response.created_at,
        )
        participant_receiver = Participant.objects.create(
            thread=thread,
            user=response.receiver,
            opponent=self.request.user,
            last_response=response,
            is_read=False,
            deleted_at=response.created_at,
        )

        context = {
            "user": response.receiver,
            "item": thread.item,
            "participant": participant_receiver,
            "protocol": self.request.scheme,
            "domain": get_current_site(self.request).domain,
        }
        message = render_to_string("email/contact_author_message.txt", context)
        send_mail(
            "お問い合わせがありました", message, settings.DEFAULT_FROM_EMAIL, [response.receiver]
        )

        return Response(
            ParticipantLSerializer(participant_sender).data,
            status=status.HTTP_201_CREATED,
        )

    @action(["get"], detail=False)
    def unconfirmed(self, request, *args, **kwargs):
        return Response(
            list(
                Participant.objects.filter(user=self.request.user)
                .filter(is_deleted=False)
                .filter(is_read=False)
                .filter(updated_at__gt=self.request.user.direct_confirmed_at)
                .values_list("id", flat=True)
            )
        )

    @action(["post"], detail=True, url_path="mark-delete")
    def mark_delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_200_OK)


class ResponseViewSet(viewsets.ModelViewSet):
    queryset = DirectResponse.objects.all()
    serializer_class = ResponseLSerializer
    pagination_class = ResponsePagination

    def list(self, request, *args, **kwargs):
        participant_id = self.request.query_params.get("participant_id", None)
        participant = get_object_or_404(
            Participant.objects.select_related("thread"), id=participant_id
        )
        queryset = (
            self.queryset.select_related("sender")
            .prefetch_related("sender__image")
            .filter(thread=participant.thread)
            .filter(created_at__gte=participant.deleted_at)
            .exclude(~Q(sender=self.request.user), receiver__isnull=True)
            .reverse()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def save_response(self, is_blocked):
        receiver = None
        if not is_blocked:
            receiver = self.request.data["receiver_id"]

        response = DirectResponse.objects.create(
            thread_id=self.request.data["thread_id"],
            sender=self.request.user,
            receiver_id=receiver,
            content=self.request.data["content"],
        )
        return response

    def update_participant(self, participant, response):
        participant.last_response = response
        participant.updated_at = response.created_at
        participant.is_deleted = False
        if participant.user != self.request.user:
            participant.is_read = False
        participant.save()

    def create(self, request, *args, **kwargs):
        blocked = (
            Block.objects.filter(user=self.request.user)
            .filter(target_id=self.request.data["receiver_id"])
            .exists()
        )
        is_blocked = (
            Block.objects.filter(user_id=self.request.data["receiver_id"])
            .filter(target=self.request.user)
            .exists()
        )

        if blocked:
            raise exceptions.ValidationError()

        if not is_blocked:
            response = self.save_response(is_blocked=False)

            participants = response.thread.participant_set.all()
            participant_sender = participants.get(user=self.request.user)
            participant_receiver = participants.get(user=response.receiver)

            self.update_participant(participant_sender, response)
            self.update_participant(participant_receiver, response)
        else:
            response = self.save_response(is_blocked=True)

            participants = response.thread.participant_set.all()
            participant_sender = participants.get(user=self.request.user)

            self.update_participant(participant_sender, response)

        data = {
            "response": ResponseLSerializer(response).data,
            "participant": ParticipantLSerializer(participant_sender).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)
