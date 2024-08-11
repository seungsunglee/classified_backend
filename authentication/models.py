from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sorl.thumbnail import get_thumbnail, delete


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email,
            username=username,
            password=password,
        )
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(_("メールアドレス"), max_length=255, unique=True)
    username = models.CharField(_("ニックネーム"), max_length=30)
    introduction = models.TextField(_("自己紹介"), max_length=150, null=True, blank=True)
    website = models.URLField(_("ウェブサイト"), null=True, blank=True)
    email_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    direct_confirmed_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_superuser


class Image(models.Model):
    user = models.OneToOneField("authentication.User", on_delete=models.CASCADE)
    file = models.ImageField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            tmp_file_name = self.file.name
            if self.file.width > 600 or self.file.height > 600:
                new_width = 600
                new_height = 600

                resized = get_thumbnail(
                    self.file, "{}x{}".format(new_width, new_height)
                )
                name = resized.name.split("/")[-1]
                self.file.save(name, ContentFile(resized.read()), True)
                delete(tmp_file_name)


@receiver(post_delete, sender=Image)
def delete_image(sender, instance, **kwargs):
    delete(instance.file.name)


class Bookmark(models.Model):
    user = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="bookmarks"
    )
    item = models.ForeignKey("classifieds.Item", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "item"]


class Block(models.Model):
    user = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="blocks"
    )
    target = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "target"]

    def __str__(self):
        return self.user.username
