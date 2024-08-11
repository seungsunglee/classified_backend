from django.db import models
from django.utils import timezone


class Thread(models.Model):
    item = models.ForeignKey(
        "classifieds.Item", on_delete=models.SET_NULL, null=True, blank=True
    )


class Response(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sender",
    )
    receiver = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receiver",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]


class Participant(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    user = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    opponent = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opponent",
    )
    last_response = models.ForeignKey(
        "direct.Response", on_delete=models.CASCADE, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["updated_at"]

    def __str__(self):
        return self.user.username
