import sys
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from auths.image_processing import generate_thumbnail
from auths.manager import UserManager


class User(AbstractUser):
    class Meta:
        db_table = "User"
        verbose_name_plural = "Users"
        managed = True
        ordering = ["date_joined"]

    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    email = models.EmailField(unique=False, null=False, blank=False)
    image = models.ImageField(upload_to="user_images/", blank=True, null=True)
    phone_number = models.PositiveBigIntegerField(blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True)
    withdraw_pin = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Withdraw Password"
    )
    refer_code = models.CharField(max_length=15, unique=True)
    refer_parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reference_parent",
    )
    forget_password = models.CharField(
        max_length=100, default=uuid.uuid4, null=True, blank=True
    )
    objects = UserManager()
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["password"]

    def delete(self, using=None, keep_parents=False):
        self.image.storage.delete(self.image.name)
        super().delete()

    def generate_short_uuid(self, length=10):
        generated_uuid = str(uuid.uuid4())
        uuid_numbers_only = ''.join(filter(str.isdigit, str(generated_uuid)))
        return uuid_numbers_only[:length]

    def save(self, *args, **kwargs):
        if not self.id:
            refer_id = self.generate_short_uuid(6)
            self.refer_code = refer_id
            print(self.refer_code)
        if not self.username and not self.id:
            user_name = "username" + str(self.phone_number)
            self.username = user_name
            super().save(*args, **kwargs)
        elif self.id and self.image:
            output = generate_thumbnail(self.image, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
        super().save(*args, **kwargs)

    def create_user(phone, password, reference, **extra_fields):
        add_user = User(
            phone_number=phone,
            password=password,
            refer_parent=reference,
            **extra_fields
        )
        password = add_user.set_password(password)
        add_user.save()
        return add_user

    def __str__(self):
        return self.username
