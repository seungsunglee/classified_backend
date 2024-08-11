from collections import OrderedDict

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import generics, viewsets, pagination, exceptions, views, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    TypeRSerializer,
)
from .models import Type, Option, PaymentHistory
from .tasks import delete_promotion

from classifieds.models import Item, Promotion
from classifieds.serializers import ItemLSerializer

import stripe


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()

    def get_serializer_class(self):
        return TypeRSerializer


class ItemRetrieveView(generics.RetrieveAPIView):
    serializer_class = ItemLSerializer
    queryset = Item.objects.all()

    def retrieve(self, request, *args, **kwargs):
        data = {}

        item = get_object_or_404(Item, pk=kwargs.get("pk"))
        item_promotions = item.promotion_set.values_list("type__slug", flat=True)

        original_option_ids = item.category.promotions.values_list(
            "option__id", flat=True
        )
        selected_option_ids = self.request.query_params.get("option_id").split(",")

        selected_options = []
        for option in Option.objects.select_related("type").filter(
            id__in=selected_option_ids
        ):
            if (
                option.id in original_option_ids
                and option.type.slug
                not in (
                    selected_option.type.slug for selected_option in selected_options
                )
                and option.type.slug not in item_promotions
            ):
                selected_options.append(option)

        valid_option_ids = []
        valid_options = []
        total_price = 0
        for option in selected_options:
            valid_option_ids.append(option.id)
            valid_options.append(
                {
                    "id": option.id,
                    "name": option.type.name,
                    "term": option.term,
                    "price": str(option.price),
                }
            )
            total_price += option.price

        data["item"] = self.get_serializer(item).data
        data["option_ids"] = valid_option_ids
        data["options"] = valid_options
        data["total_price"] = total_price
        data["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        return Response(data)


class CreateCheckoutSessionView(views.APIView):
    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        item_id = self.request.data.get("item_id")
        option_ids = self.request.data.get("option_ids")
        total_price = self.request.data.get("total_price")
        cancel_url = self.request.data.get("cancel_url")

        line_items = []
        for option_id in option_ids:
            option = get_object_or_404(Option, id=option_id)
            line_items.append(
                {
                    "price_data": {
                        "currency": "aud",
                        "product_data": {"name": option.type.name},
                        "unit_amount": int(option.price * 100),
                    },
                    "quantity": 1,
                }
            )

        protocol = self.request.scheme
        domain = get_current_site(self.request).domain

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                metadata={
                    "item_id": item_id,
                    "option_ids": ",".join(map(str, option_ids)),
                    "total_price": total_price,
                },
                success_url="%s://%s/promotion/success" % (protocol, domain),
                cancel_url="%s://%s%s" % (protocol, domain, cancel_url),
            )
            return Response({"id": checkout_session.id})
        except Exception as e:
            pass
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


class ExecuteView(views.APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event["type"] == "checkout.session.completed":
            item = get_object_or_404(
                Item, id=event["data"]["object"]["metadata"]["item_id"]
            )

            options = []
            for option_id in event["data"]["object"]["metadata"]["option_ids"].split(
                ","
            ):
                option = get_object_or_404(Option, id=option_id)
                options.append(option)

                disabled_at = timezone.now() + timezone.timedelta(days=option.term)

                promotion = Promotion.objects.create(
                    item=item, type=option.type, disabled_at=disabled_at
                )

                # celery
                delete_promotion.apply_async([promotion.id], eta=disabled_at)

            payment_history = PaymentHistory.objects.create(
                payment_intent=event["data"]["object"]["payment_intent"],
                user=item.author,
                item=item,
                total_price=event["data"]["object"]["metadata"]["total_price"],
            )
            payment_history.options.set(options)

        return Response(status=status.HTTP_200_OK)
