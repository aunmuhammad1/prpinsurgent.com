from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.signals import post_save
from django.shortcuts import redirect
from django.core.cache import cache

from account.models import income, wallet
from auths.models import User


def validate_data(phone):
    try:
        if User.objects.get(phone_number=phone):
            messages = "Phone number is already exist"
        return messages
    except Exception:
        return None


def login_validate(phone, Password):
    try:
        message = None
        user = User.objects.get(phone_number=phone)
        if user.is_active == False:
            message = "You Account is deactivated"
        elif check_password(Password, user.password) == False:
            message = "Invalid Phone number or Password"
        return message, user
    except Exception as e:
        message = "Invalid Phone number or Password"
        return message, None

def admin_login_as_user(id):
    try:
        message = None
        user = User.objects.get(id=id)
        if user.is_active == False:
            message = "Account is deactivated"
        return message, user
    except Exception as e:
        message = "Invalid user Id"
        return message, None

def change_password_validate(self, id, current_password, new_password):
    try:
        message = None
        user = User.objects.get(id=id)
        if user.is_active == False:
            message = "You Account is deactivated"
        elif check_password(current_password, user.password) == False:
            message = "Invalid current Password"
        else:

            user.set_password(new_password)
            user.save()
            # Update the session with the new password hash
            update_session_auth_hash(self.request, user)
        return message
    except Exception as e:
        message = "Invalid user id or user not found"
        return message


def change_transaction_pin_validate(self, id, current_password, transaction_pin):
    try:
        message = None
        user = User.objects.get(id=id)
        if user.is_active == False:
            message = "You Account is deactivated"
        elif check_password(current_password, user.password) == False:
            message = "Invalid current Password"
        else:
            user.withdraw_pin = transaction_pin
            user.save()
        return message
    except Exception as e:
        message = "Invalid user id or user not found"
        return message


def is_valid_refer_code(reference):
    try:
        uuid_obj = reference
        uuid_obj = str(uuid_obj)
        if User.objects.filter(refer_code=uuid_obj, is_active=True):
            refer_user = User.objects.get(refer_code=uuid_obj, is_active=True)
            return refer_user, None
        else:
            messages = "Enter invalid Reference Code"
            return None, messages
    except ValueError:
        messages = "Enter invalid Reference Code"
        return None, messages


def user_post_save(*args, **kwargs):
    cache.clear()
    user = User.objects.get(username=kwargs.get("instance"))
    join_income = income.objects.filter(
        refer_user=user,
        income_resource="Reference Join Income",
    )
    if not wallet.objects.filter(user=kwargs.get("instance")):
        wallet.create_user_wallet(user)
    if user.refer_parent and not join_income:
        join_income_count = User.objects.filter(
            refer_parent__id=user.refer_parent.id
        ).count()
        # if join_income_count < 21:
        #     income.create_user_income(
        #         5, user.refer_parent, "Reference Join Income", None, user, "Level 1"
        #     )


post_save.connect(user_post_save, sender=User)


class Login_Check:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, **arg):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("/admin_dashboard/")
            elif request.user.is_superuser == False and request.user.is_staff == False:
                return redirect("/")
        response = self.get_response(request)
        return response


class UserLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/signup/"

    def handle_no_permission(self):
        return self.redirect_to_login(self.request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("/admin_dashboard/")
        else:
            login_url = self.login_url
            nextpage_url = self.request.get_full_path()
            full_path = str(login_url + "?next=" + nextpage_url)
            return redirect(full_path)
        return super().dispatch(request, *args, **kwargs)


class AdminLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/signup/"

    def handle_no_permission(self):
        return self.redirect_to_login(self.request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser == False:
                return redirect("/")
            elif request.user.is_active == False:
                messages.error(request, "Your account is deactivated by our team")
                return redirect("/signup/")
        else:
            login_url = self.login_url
            nextpage_url = self.request.get_full_path()
            full_path = str(login_url + "?next=" + nextpage_url)
            return redirect(full_path)
        return super().dispatch(request, *args, **kwargs)


class RequiredLoginRequiredMixin:
    def handle_no_permission(self):
        return self.redirect_to_login(self.request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("/admin_dashboard/")
            elif request.user.is_superuser == False and request.user.is_staff == False:
                return redirect("/")
        return super().dispatch(request, *args, **kwargs)
