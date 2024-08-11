from django.db import models


class Location(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    name_with_postcode = models.CharField(max_length=255, null=True, blank=True)
    name_with_postcode_and_state = models.CharField(
        max_length=255, null=True, blank=True
    )
    state_code = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    level = models.IntegerField(default=1, null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name
