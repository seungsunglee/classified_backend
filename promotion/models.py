from django.db import models
from django.utils import timezone


class Type(models.Model):
    class SlugType(models.TextChoices):
        FIXED = "fixed", "FIXED"
        HIGHLIGHT = "highlight", "HIGHLIGHT"

    slug = models.CharField(max_length=255, choices=SlugType.choices)
    name = models.CharField(max_length=255)
    description = models.TextField()
    index = models.IntegerField()
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        return "%s (%s)" % (self.name, self.note)


class Option(models.Model):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    term = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["term"]

    def __str__(self):
        return "%s $%s (%s days)" % (self.type, self.price, self.term)


class PaymentHistory(models.Model):
    payment_intent = models.CharField(max_length=255)
    user = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    item = models.ForeignKey(
        "classifieds.Item", on_delete=models.SET_NULL, null=True, blank=True
    )
    options = models.ManyToManyField(Option, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
