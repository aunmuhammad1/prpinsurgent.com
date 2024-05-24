import uuid
import random

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from admin_panel.models import company_profile
from auths import helper
from auths.helper import RequiredLoginRequiredMixin
from auths.models import User


class Login(RequiredLoginRequiredMixin, View):
    def get(self, request):
        Data = {}
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "login.html", Data)

    def post(self, request):
        Data = request.POST
        phone = Data.get("phone")
        Password = Data.get("password")
        message, user = helper.login_validate(phone, Password)
        if message != None:
            messages.error(request, message)
            return redirect("/login/")
        else:
            login(request, user)
            if request.user.is_superuser:
                return redirect("/admin_dashboard/")
            else:
                request.session["popup_shown"] = True
                return redirect("/")


class Sign_Up(RequiredLoginRequiredMixin, View):
    def get(self, request):
        ref_id = request.GET.get("code", "")
        print(ref_id)
        verify_number = random.randint(1012, 9999)
        request.session["verify_code"] = verify_number
        verify_code = [int(digit) for digit in str(verify_number)]
        Data = {"ref_id": ref_id, "verify_code": verify_code}
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "signup.html", Data)

    def post(self, request):
        Data = request.POST
        phone = Data.get("phone")
        password = Data.get("password")
        email = Data.get("email", None)
        reference = Data.get("reference", None)
        verify_code = Data.get("verify_code", None)
        # user_email = User.objects.filter(email=email)
        if request.session["verify_code"] != int(verify_code):
            message = "Invalid Verification Code"
            messages.error(request, message)
            return redirect("/signup/")
        # if user_email:
        #     message = "Email is already used"
        #     messages.error(request, message)
        #     return redirect("/signup/")
        if reference != "":
            refer_user, message = helper.is_valid_refer_code(reference)
            if message != None:
                messages.error(request, message)
                return redirect("/signup/?ref_id=" + reference + "/")
            else:
                reference = refer_user
        else:
            reference = None
        message = helper.validate_data(phone)
        if message != None:
            messages.error(request, message)
        else:
            User.create_user(phone, password, reference)
            messages.success(
                request, "Account Created"
            )
            user = User.objects.get(phone_number=phone)
            login(request, user)
            return redirect("/")
        return redirect("/signup/")


class Forgetpassword(RequiredLoginRequiredMixin, View):
    def get(self, request):
        return render(request, "forgetpassword.html")

    def post(self, request):
        Data = request.POST
        phone = Data.get("phone")
        email = Data.get("email", None)

        if User.objects.filter(phone_number=phone, email=email).exists():
            user_data = User.objects.get(phone_number=phone, email=email)
            user_data.forget_password = uuid.uuid4()
            forgetPassword = user_data.forget_password
            user_data.save()
            return render(
                request, "changepassword.html", {"forgetPassword": forgetPassword}
            )
        messages.error(request, "Invalid Phone number or Email")
        return render(request, "forgetpassword.html")


class Changepassword(View):
    def get(self, request):
        return redirect("/login/forgetpassword/")

    def post(self, request):
        Data = request.POST
        new_password = Data.get("password", None)
        forgetPassword = Data.get("forgetPassword", None)

        if new_password and forgetPassword:
            if User.objects.filter(forget_password=forgetPassword).exists():
                user = User.objects.get(forget_password=forgetPassword)
                user.set_password(new_password)
                user.forget_password = uuid.uuid4()
                user.save()
                messages.success(
                    request, "Password is changed successfully, please login now"
                )
                return redirect("/login/")
        return redirect("/login/forgetpassword/")
