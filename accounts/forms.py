from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.utils.translation import gettext, gettext_lazy as _

User = get_user_model()


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'introduction', 'website',)


class PasswordChangeForm(DjangoPasswordChangeForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )