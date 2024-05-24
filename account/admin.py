from django import forms
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from account.models import (add_bank, bank_detail, deposit, deposit_image,
                            income, plan, user_plan, wallet, withdraw, LastIncome, votes)

# Register your models here.


class UserWalletFormValidation(forms.ModelForm):
    def clean(self):
        user_wallet = self.data["user"]
        try:
            wallet.objects.get(user=user_wallet)
        except ObjectDoesNotExist as e:
            raise forms.ValidationError(
                {"user": "Request User Wallet Not Found"})


class WalletBalenceFormValidation(forms.ModelForm):
    def clean(self):
        user_wallet = self.cleaned_data.get("user")
        Withdraw_amount = self.cleaned_data.get("withdraw_amount")
        Status = self.cleaned_data.get("status")
        try:
            Wallet = wallet.objects.get(user=user_wallet)
            if Wallet.balance < int(Withdraw_amount) and Status != "Withdraw Failed":
                raise forms.ValidationError(
                    {"withdraw_amount": "Your Wallet have insufficient balance"}
                )
            elif Withdraw_amount < 680:
                raise forms.ValidationError(
                    {"withdraw_amount": "Minimium Withdraw is 680 Rs"}
                )
        except ObjectDoesNotExist as e:
            raise forms.ValidationError(
                {"user": "Request User Wallet Not Found"})


class buyUserPlanFormValidation(forms.ModelForm):
    def clean(self):
        user_wallet = self.cleaned_data.get("user")
        buy_plan = self.cleaned_data.get("plan")
        try:
            Wallet = wallet.objects.get(user=user_wallet)
            Plan_price = plan.objects.get(name=buy_plan)
            if Wallet.balance < Plan_price.price:
                raise forms.ValidationError(
                    {"plan": "Your Wallet have insufficient balance to buy this plan"}
                )
        except ObjectDoesNotExist as e:
            raise forms.ValidationError(
                {"user": "Request User Wallet Not Found"})


class walletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "created_at", "id"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username"]
    readonly_fields = ["updated_at", "created_at"]

class voteAdmin(admin.ModelAdmin):
    list_display = ["plan","user", "vote", "vote_at", "id"]
    list_filter = ["plan__name", "vote", "vote_at"]
    search_fields = ["user__username", "plan__name"]
    readonly_fields = ["vote_at"]


class planAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "plan_duration",
                    "total_income", "is_launch", "id"]
    readonly_fields = ["daily_income", "hourly_income"]


class userPlanAdmin(admin.ModelAdmin):
    form = buyUserPlanFormValidation
    list_display = ["plan", "user", "status", "id"]
    search_fields = ["user__username"]
    readonly_fields = ["started_at", "completed_at"]
    list_filter = ["status"]


class withdrawAdmin(admin.ModelAdmin):
    form = WalletBalenceFormValidation
    list_display = [
        "user",
        "withdraw_amount",
        "amount_received",
        "status",
        "withdraw_request_at",
        "id",
    ]
    # readonly_fields = [
    #     "withdraw_request_at",
    #     "approved_or_rejected_at",
    #     "amount_received",
    # ]
    search_fields = ["user__username"]
    list_filter = ["status", "withdraw_request_at"]

    def save_model(self, request, obj, form, change):
        try:
            obj.save()

            # Display success message
            self.message_user(
                request, "Custom success message", level="success")

        except Exception as e:
            # Display error message
            self.message_user(
                request, f"Custom error message: {str(e)}", level="error")

        # Rest of the save_model logic
        super().save_model(request, obj, form, change)


class depositAdmin(admin.ModelAdmin):
    form = UserWalletFormValidation
    filter_horizontal = ("images",)

    list_display = ["user", "amount", "status", "deposit_request_at", "id"]
    search_fields = ["user__username"]
    readonly_fields = ["deposit_request_at", "approved_or_rejected_at"]
    list_filter = ["status", "deposit_request_at"]


class incomeAdmin(admin.ModelAdmin):
    form = UserWalletFormValidation
    list_display = [
        "user",
        "amount",
        "income_resource",
        "refer_user",
        "user_level",
        "income_at",
        "id",
    ]
    search_fields = ["user__username"]
    readonly_fields = ["income_at"]
    list_filter = ["income_resource", "amount", "income_at"]


class deposit_imageAdmin(admin.ModelAdmin):
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<image style="height:30px;border-radius:30px" src="{}" />'.format(
                    obj.image.url
                )
            )
        else:
            return None

    list_display = ["image_preview", "id"]
    readonly_fields = ["image_preview"]


class bank_detailAdmin(admin.ModelAdmin):
    list_display = ["account_title", "bank_id", "id"]
    list_filter = ["bank_id"]
    search_fields = ["account_title", "user__username"]


class bankAdmin(admin.ModelAdmin):
    list_display = ["bank_name", "created_at", "id"]


admin.site.register(wallet, walletAdmin)
admin.site.register(plan, planAdmin)
admin.site.register(user_plan, userPlanAdmin)
admin.site.register(deposit, depositAdmin)
admin.site.register(withdraw, withdrawAdmin)
admin.site.register(votes, voteAdmin)
admin.site.register(income, incomeAdmin)
admin.site.register(deposit_image, deposit_imageAdmin)
admin.site.register(bank_detail, bank_detailAdmin)
admin.site.register(add_bank, bankAdmin)
admin.site.register(LastIncome)
