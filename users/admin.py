from django.contrib import admin

from users.models import notification

# Register your models here.


class notificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "is_open", "created_at", "id"]
    list_filter = ["created_at"]


admin.site.register(notification, notificationAdmin)
