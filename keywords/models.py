from django.db import models


class Keyword(models.Model):
    title = models.CharField(max_length=255)
    roman_alphabet = models.CharField(max_length=255)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
