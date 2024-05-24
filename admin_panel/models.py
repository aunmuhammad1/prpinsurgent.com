import sys
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from auths.image_processing import generate_thumbnail


# Create your models here.
class company_profile(models.Model):
    class Meta:
        db_table = "company_profile"
        verbose_name_plural = "company_profiles"
        managed = True
        ordering = ["-id"]

    company_name = models.CharField(max_length=200)
    company_logo = models.ImageField(upload_to="company_logo/", blank=True, null=True)
    company_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def delete(self, using=None, keep_parents=False):
        self.company_logo.storage.delete(self.company_logo.name)
        super().delete()

    def save(self, *args, **kwargs):
        if self.company_logo and not self.id:
            output = generate_thumbnail(self.company_logo, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
        if self.company_logo and self.id:
            old_data = company_profile.objects.get(id=self.id)
            output = generate_thumbnail(self.company_logo, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
            # old_data.image.storage.delete(old_data.company_logo.name)
        super().save(*args, **kwargs)

    def create_company_profile(company_name, company_logo, company_address):
        try:
            company_profile(
                company_name=company_name,
                company_logo=company_logo,
                company_address=company_address,
            ).save()
            return None
        except Exception as e:
            return e

    def __str__(self):
        return self.company_name


class whatsapp_group_link(models.Model):
    class Meta:
        db_table = "whatsapp_group_link"
        verbose_name_plural = "whatsapp_group_links"
        managed = True
        ordering = ["-id"]

    join_link = models.CharField(max_length=200)
    telegram_link = models.URLField(blank=True)
    phone_number = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def create_social_media_link(join_link, telegram_link, phone_number):
        try:
            whatsapp_group_link(join_link=join_link, phone_number=phone_number, telegram_link=telegram_link).save()
            return None
        except Exception as e:
            return e

    def __str__(self):
        return self.join_link
