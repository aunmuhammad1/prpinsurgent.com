from django.contrib import admin
from django.utils.html import format_html

from admin_panel.models import company_profile, whatsapp_group_link


# Register your models here.
class comapany_profileAdmin(admin.ModelAdmin):
    def image_preview(self, obj):
        if obj.company_logo:
            return format_html(
                '<image style="height:40px;" src="{}" />'.format(obj.company_logo.url)
            )
        else:
            return None

    list_display = ["image_preview", "company_name", "created_at", "id"]


class whatsapp_group_linkAdmin(admin.ModelAdmin):
    list_display = ["id", "join_link", "phone_number"]


admin.site.register(company_profile, comapany_profileAdmin)
admin.site.register(whatsapp_group_link, whatsapp_group_linkAdmin)
