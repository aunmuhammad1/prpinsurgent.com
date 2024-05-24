from django.db import models

from auths.models import User

# Create your models here.


class notification(models.Model):
    class Meta:
        db_table = "notification"
        verbose_name_plural = "notifications"
        managed = True
        ordering = ["-created_at"]

    Title = (
        ("Withdraw Success", "Withdraw Success"),
        ("Withdraw Failed", "Withdraw Failed"),
        ("Recharge Success", "Recharge Success"),
        ("Recharge Failed", "Recharge Failed"),
        ("Withdraw Request", "Withdraw Request"),
        ("Recharge Request", "Recharge Request"),
    )
    title = models.CharField(max_length=100, choices=Title)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_notifications"
    )
    user_number = models.CharField(max_length=200, blank=True, null=True)
    notification_body = models.TextField()
    is_open = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def create_user_notification(user, notification_title, notification_body):
        add_notification = notification(
            user=user, title=notification_title, notification_body=notification_body
        ).save()
        return add_notification

    def save(self, *args, **kwargs):
        from account.helper import convert_middle_to_asterisk

        if not self.id:
            self.user_number = convert_middle_to_asterisk(int(self.user.phone_number))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username
