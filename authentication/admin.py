from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from .models import User, Image, Bookmark, Block


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("email", "username")

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "username", "password", "is_active", "is_superuser")


class ImageInline(admin.StackedInline):
    model = Image


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "email",
        "username",
        "is_superuser",
        "is_active",
        "last_login",
        "date_joined",
        "direct_confirmed_at",
    )
    list_filter = (
        "is_superuser",
        "is_active",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "username",
                    "password",
                    "is_active",
                    "direct_confirmed_at",
                )
            },
        ),
        ("Permissions", {"fields": ("is_superuser",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()
    inlines = (ImageInline,)


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "item")


class BlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "target",
    )


admin.site.register(User, UserAdmin)
admin.site.register(Image)
admin.site.unregister(Group)
admin.site.register(Bookmark, BookmarkAdmin)
admin.site.register(Block, BlockAdmin)
