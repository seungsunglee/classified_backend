from django import forms
from django.contrib.auth.forms import (
    SetPasswordForm as DjangoSetPasswordForm,
    PasswordChangeForm as DjangoPasswordChangeForm,
)
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext, gettext_lazy as _

from .models import Category, Item


class ItemForm(forms.ModelForm):
    location_autocomplete = forms.CharField()

    def __init__(self, *args, **kwargs):
        category_id = kwargs.pop("category_id")
        super().__init__(*args, **kwargs)

        category = get_object_or_404(Category, id=category_id)

        for attribute in category.field_attributes.all():
            if attribute.slug == "rent":
                self.fields["attributes_rent"] = forms.DecimalField()

    class Meta:
        model = Item
        fields = (
            "title",
            "description",
            "location",
            "location_autocomplete",
        )
