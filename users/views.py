import os
import random

from datetime import timedelta, datetime
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from account import helper
from account.helper import convert_middle_to_asterisk
from account.models import (add_bank, bank_detail, deposit, income, plan,
                            user_plan, wallet, withdraw, LastIncome)
from admin_panel.models import company_profile, whatsapp_group_link
from auths.helper import UserLoginRequiredMixin as LoginRequiredMixin
from auths.helper import (change_password_validate,
                          change_transaction_pin_validate)
from auths.models import User
from users.management.commands.plan_income import plan_income_task, plan_income_task1
from users.models import notification


class plan_income(View):
    def get(self, request):
        if LastIncome.objects.filter(name="plan income").exists():
            last_income = LastIncome.objects.latest('id')
            time_diff = timezone.now() - last_income.last_paln_income
            if time_diff > timedelta(minutes=20):
                last_income.last_paln_income = timezone.now()
                plan_income_task()
                LastIncome.update_lastincome(last_income.id)
        else:
            last_income = LastIncome.objects.create(last_paln_income=timezone.now()).save()
            plan_income_task()
        return redirect("/")

# Create your views here.
class Home(LoginRequiredMixin, View):
    login_url = "/login/"
    def get(self, request):
        if LastIncome.objects.filter(name="plan income").exists():
            last_income = LastIncome.objects.latest('id')
            time_diff = timezone.now() - last_income.last_paln_income
            if time_diff > timedelta(minutes=20):
                last_income.last_paln_income = timezone.now()
                plan_income_task1()
                LastIncome.update_lastincome(last_income.id)
        else:
            last_income = LastIncome.objects.create(last_paln_income=timezone.now()).save()
            plan_income_task1()

        today = timezone.now().date()
        today1 = datetime.now().date()
        user_wallet = wallet.objects.get(user=request.user.id)
        User_plans = user_plan.objects.filter(user__id=request.user.id).order_by(
            "plan__price"
        )
        total_recharge = deposit.objects.filter(
            user=request.user,
            status="Deposit Success",
        ).aggregate(total_deposit=(Sum("amount")))

        total_withdraw = withdraw.objects.filter(
            user=request.user,
            status="Withdraw Success",
        ).aggregate(total_cashout=(Sum("withdraw_amount")))

        total_team_income = income.objects.filter(
            Q(income_resource="Reference Income")
            | Q(income_resource="Reference Join Income")
            | Q(income_resource="Reference CashBack"),
            user=request.user,
        ).aggregate(team_income=(Sum("amount")))

        total_earning = income.objects.filter(
            user=request.user,
        ).aggregate(total_income=(Sum("amount")))

        total_check_reward = income.objects.filter(
            income_resource="Daily Reward",
            user=request.user,
        ).aggregate(check_reward=(Sum("amount")))
        if total_check_reward["check_reward"] == None:
            total_check_reward["check_reward"] = 0
        
        User_plans_count = user_plan.objects.filter(
            user__id=request.user.id, status="In Process"
        ).count()

        plans = plan.objects.all().order_by("price")
        plan_buy_count = [sum(1 for j in User_plans if i.id == j.plan.id) for i in plans]

        active_plans = user_plan.objects.filter(user=request.user).exists
        daily_reward_cal = [] 
        daily_reward_date = ((timezone.now().date() - request.user.date_joined.date()).days) % 7
        back_reward_date = timezone.now().date() - timedelta(days=int(daily_reward_date))
        today_reward = timezone.now().date()
        for i in range(0,7):
            daily_reward_cal.append(back_reward_date + timedelta(days=int(i)))

        daily_reward = income.objects.filter(
               Q(income_at__date=today)|
               Q(income_at__date=today1), 
               income_resource="Daily Reward", 
               user=request.user,
        ).exists()

        Data = {
            "user_wallet": user_wallet,
            "all_plans": plans,
            "plan_buy_count": plan_buy_count,
            "total_recharge": total_recharge["total_deposit"],
            "total_withdraw": total_withdraw["total_cashout"],
            "total_team_income": total_team_income["team_income"],
            "total_earning": total_earning["total_income"],
            "daily_reward" : daily_reward,
            "today_reward" : today_reward,
            "daily_reward_cal" : daily_reward_cal,
            "total_check_reward" : total_check_reward["check_reward"],
            "User_plans_count": User_plans_count,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "home.html", Data)


class Recharge(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        four_days_ago = timezone.now().date() - timedelta(days=4)
        Notifications = notification.objects.filter(
            user=request.user, created_at__gte=four_days_ago
        ).order_by("-created_at")
        new_notification = notification.objects.filter(
            user=request.user, is_open=False
        ).count()
        Data = {
            "user_wallet": user_wallet,
            "Notifications": Notifications,
            "new_notification": new_notification,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "recharge.html", Data)

    def post(self, request, *args):
        try:
            data = request.POST
            recharge_amount = data.get("recharge_amount", None)
            payment_method = data.get("payment_method", None)
            image = request.FILES.getlist("images", None)
            change_number = data.get("change_number", None)
            target_trans_id = data.get("tp", None)
            user_wallet = wallet.objects.get(user=request.user.id)

            request.session['target_trans_id'] = target_trans_id
            four_days_ago = timezone.now().date() - timedelta(days=4)
            five_second_ago = timezone.now() - timedelta(seconds=5)
            if int(recharge_amount) < 1200:
                   messages.success(
                        request,
                        "Minimium Recharge Rs 1200",
                    )
            elif image:
                if deposit.objects.filter(
                    user=request.user, deposit_request_at__gte=five_second_ago
                ):
                    pass
                else:
                    deposit.create_deposit_request(
                        recharge_amount, request.user.id, image
                    )
                    messages.success(
                        request,
                        "Successfully",
                    )
                
                    return redirect('/onepayPostDeposit/')
            elif recharge_amount and payment_method == None:
                account_list = []
                admin = User.objects.filter(is_superuser=True).first()
                admin_accounts = bank_detail.objects.filter(user=admin, is_deleted=False)
                account_details = None
                order_id= None
                if admin_accounts:
                    for i in admin_accounts:
                        account_list.append(i.id)
                    random.shuffle(account_list)
                    random_account = random.choice(account_list)
                    account_details = bank_detail.objects.get(id=random_account)
                    request.session['account_details'] = {
                        'id': account_details.id,
                        'account_number': account_details.account_number,
                        'account_title': account_details.account_title,
                        'bank_name': account_details.bank_id.bank_name,
                    }
                order_id_1 = random.randint(1234567890, 9999999890)
                order_id_2 = random.randint(123456780, 999999989 )
                order_id = str(order_id_1) + str(order_id_2)
                pre_target_datetime = datetime.now() + timedelta(minutes=5)
                request.session['pre_target_datetime'] = pre_target_datetime.isoformat()
                target_datetime = datetime.now() + timedelta(minutes=30)
                request.session['target_datetime'] = target_datetime.isoformat()
                Data = {"recharge_amount": recharge_amount, "account_details": account_details, "order_id":order_id}
                return render(request, "one-pay.html", Data)
            elif recharge_amount and payment_method and change_number:
                account_list = []
                account_details = None
                admin = User.objects.filter(is_superuser=True).first()
                admin_accounts = bank_detail.objects.filter(user=admin).exclude(id=change_number)
                print(admin_accounts, '\n\n')
                if admin_accounts:
                    for i in admin_accounts:
                        account_list.append(i.id)
                    random.shuffle(account_list)
                    random_account = random.choice(account_list)
                    account_details = bank_detail.objects.get(id=random_account)
                    request.session['account_details'] = {
                        'id': account_details.id,
                        'account_number': account_details.account_number,
                        'account_title': account_details.account_title,
                        'bank_name': account_details.bank_id.bank_name,
                    }
                    target_datetime = datetime.now() + timedelta(minutes=30)
                    request.session['target_datetime'] = target_datetime.isoformat()
                Data = {"recharge_amount": recharge_amount, "account_details": account_details}
                if company_profile.objects.all():
                        Company_profile = company_profile.objects.all().first()
                        Data["Company_profile"] = Company_profile
                return render(request, "account_details.html", Data)
            elif recharge_amount and payment_method:
                account_list = []
                admin = User.objects.filter(is_superuser=True).first()
                admin_accounts = bank_detail.objects.filter(user=admin, is_deleted=False)

                if admin_accounts:
                    for i in admin_accounts:
                        account_list.append(i.id)
                    random.shuffle(account_list)
                    random_account = random.choice(account_list)
                    Data = {
                        "recharge_amount": recharge_amount,
                        "user_wallet": user_wallet,
                    }
                    if company_profile.objects.all():
                        Company_profile = company_profile.objects.all().first()
                        Data["Company_profile"] = Company_profile
                    return render(request, "account_details.html", Data)
                else:
                    messages.error(request, "Active deposit account is not found")
        except ObjectDoesNotExist:
            return redirect("/recharge/")
        return redirect("/recharge/")

class Bank_amount_setting(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        four_days_ago = timezone.now().date() - timedelta(days=4)
        Notifications = notification.objects.filter(
            user=request.user, created_at__gte=four_days_ago
        ).order_by("-created_at")
        new_notification = notification.objects.filter(
            user=request.user, is_open=False
        ).count()
        bank_names = add_bank.objects.all()
        Data = {
            "user_wallet": user_wallet,
            "Notifications": Notifications,
            "new_notification": new_notification,
            "bank_names": bank_names,
        }
        if bank_detail.objects.filter(user__id=request.user.id):
            user_bank_account = bank_detail.objects.filter(user__id=request.user.id).first()
            Data = {
                "user_wallet": user_wallet,
                "bank_names": bank_names,
                "user_bank_account": user_bank_account,
                "Notifications": Notifications,
                "new_notification": new_notification,
            }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "bank_account_setting.html", Data)

    def post(self, request, *args):
        data = request.POST
        account_name = data.get("account_name")
        account_number = data.get("account_number")
        bank = data.get("bank", None)
        bank_account_id = data.get("id", None)
        print(account_name, account_number, request.user, bank)
        action = ""
        if bank_account_id == None:
            message = bank_detail.create_bank_detail(
                account_name, account_number, request.user, None, bank
            )
            action = "added"
        else:
            message = helper.update_bank_detail(
                account_name, account_number, bank_account_id, None ,bank
            )
            action = "updated"

        if message == None:
            messages.success(request, "Successfully")
        else:
            messages.error(request, message)
        return redirect("/account/")

class Withdraw_amount(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        user_bank_account = bank_detail.objects.filter(user__id=request.user.id)
        last_withdraw = None
   

        if user_bank_account:
            user_bank_account = bank_detail.objects.get(user__id=request.user.id)
        else:
            user_bank_account = False
     
        #     messages.error(request, "Please add bank account first")
        #     return redirect("/account/")
        # if request.user.withdraw_pin is None:
        #     messages.error(request, "Please Set your Windraw Pin First")
        #     return redirect("/user_profile/", action="pin")
        if withdraw.objects.filter(
            user__id=request.user.id, withdraw_request_at__date=timezone.now().date()
        ):
            last_withdraw = int(20)

        Data = {
            "user_wallet": user_wallet,
            "user_bank_account": user_bank_account,
            "last_withdraw": last_withdraw,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "withdraw.html", Data)

    def post(self, request, *args):
        data = request.POST
        amount = data.get("amount", None)
        bank_account = data.get("bank", None)
        bank_add = data.get("bank_add", None)
        if bank_add == "no":
            messages.error(request, "Add account first")
            return redirect("/account/")
        four_second_ago = timezone.now() - timedelta(seconds=4)
        if not user_plan.objects.filter(user=request.user, plan__price__gte=201):
            messages.error(request, "Buy atleast one paid plan")
        elif withdraw.objects.filter(
            user=request.user, withdraw_request_at__gte=four_second_ago
        ):
            messages.success(request, "Successfully")
        else:
            message = withdraw.create_withdraw_request(
                int(amount), request.user, bank_account
            )
            if message == None:
                messages.success(request, "Successfully")
            else:
                messages.error(request, message)
        return redirect("/withdraw/")


class Invest(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args):
        plans_days = []
        income_per_plan = []
        plan_buy_count = []
        total_user_income = 0
        total = 0
        plans = plan.objects.all().order_by("price")
        user_wallet = wallet.objects.get(user=request.user.id)
        User_plans = user_plan.objects.filter(user__id=request.user.id).order_by("-id")
        total_income = income.objects.filter(
            user__id=request.user.id, income_resource="My Investment Income"
        )
        four_days_ago = timezone.now().date() - timedelta(days=4)
        Notifications = notification.objects.filter(
            user=request.user, created_at__gte=four_days_ago
        ).order_by("-created_at")
        new_notification = notification.objects.filter(
            user=request.user, is_open=False
        ).count()
        for i in plans:
            count = 0
            for j in User_plans:
                if i.id == j.plan.id:
                  count = count + 1
            plan_buy_count.append(count)
         
        for j in total_income:
            total_user_income = total_user_income + j.amount
        total_user_income = round(total_user_income, 2)
        for i in User_plans:
            total_income = income.objects.filter(
                user__id=request.user.id,
                income_resource="My Investment Income",
                user_plan=user_plan.objects.get(id=i.id),
            )
            for j in total_income:
                total = float(total + j.amount)
            income_per_plan.append(total)
            total = 0
            if i.status == "In Process":
                time_diff = timezone.now() - i.started_at
                days_diff = int(time_diff.days + 1)
                plans_days.append(days_diff)
            else:
                plans_days.append(i.plan.plan_duration)
        total_user_income = sum(income_per_plan)
        total_user_income = round(total_user_income, 2)
        User_plans_count = user_plan.objects.filter(
            user__id=request.user.id, status="In Process"
        ).count()

        Data = {
            "User_plans": User_plans,
            "User_plans_count": User_plans_count,
            "all_plans": plans,
            "user_wallet": user_wallet,
            "User_plans_count": User_plans_count,
            "total_user_income": total_user_income,
            "income_per_plan": income_per_plan,
            "plans_days": plans_days,
            "plan_buy_count": plan_buy_count,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "my_invest.html", Data)

    def post(self, request, *args):
        data = request.POST
        buy_plan = data.get("plan", None)
        message = user_plan.create_user_plan(buy_plan, request.user.id)
        if message == None:
            messages.success(request, "Successfully")
        else:
            messages.error(request, message)
        return redirect("/activePlan/")


class MyBills(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        income_history = income.objects.filter(user=request.user.id).order_by("-id")
        plan_income_task1()
        Data = {
            "user_wallet": user_wallet,
            "income_history": income_history,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "history.html", Data)


class WithdrawHistory(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        deposit_history = deposit.objects.filter(user=request.user.id).order_by("-id")
        withdraw_history = withdraw.objects.filter(user=request.user.id).order_by("-id")
        income_history = income.objects.filter(user=request.user.id).order_by("-id")

        Data = {
            "user_wallet": user_wallet,
            "deposit_history": deposit_history,
            "withdraw_history": withdraw_history,
            "income_history": income_history,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "withdraw_history.html", Data)


class DepositHistory(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
        user_wallet = wallet.objects.get(user=request.user.id)
        deposit_history = deposit.objects.filter(user=request.user.id).order_by("-id")
        withdraw_history = withdraw.objects.filter(user=request.user.id).order_by("-id")
        income_history = income.objects.filter(user=request.user.id).order_by("-id")

        Data = {
            "user_wallet": user_wallet,
            "deposit_history": deposit_history,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "deposite_history.html", Data)


class Profile(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args, action=None):
        user_wallet = wallet.objects.get(user=request.user.id)
        four_days_ago = timezone.now().date() - timedelta(days=4)
        Notifications = notification.objects.filter(
            user=request.user, created_at__gte=four_days_ago
        ).order_by("-created_at")
        new_notification = notification.objects.filter(
            user=request.user, is_open=False
        ).count()
        Data = {
            "user_wallet": user_wallet,
            "Notifications": Notifications,
            "new_notification": new_notification,
            "action": action,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "user_profile.html", Data)

    def post(self, request, *args):
        data = request.POST
        email = data.get("email", None)
        username = data.get("username", None)
        #   image = request.FILES.get('images', None)
        current_password = data.get("current_password", None)
        transaction_pin = data.get("transaction_pin", None)
        new_password = data.get("new_password", None)
        user_profile = User.objects.get(id=request.user.id)

        if username:
            user_profile.username = username
            user_profile.save()
            messages.success(request, "Successfully")
        elif current_password and new_password:
            message = change_password_validate(
                self, user_profile.id, current_password, new_password
            )
            if message == None:
                messages.success(request, "Successfully")
            else:
                messages.error(request, message)
        return redirect("/user_profile/")


class WithdrawPassword(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args, action=None):
        user_wallet = wallet.objects.get(user=request.user.id)
        Data = {
            "user_wallet": user_wallet,
            "action": action,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "transaction_password.html", Data)

    def post(self, request, *args):
        data = request.POST
        current_password = data.get("current_password", None)
        transaction_pin = data.get("transaction_pin", None)
        user_profile = User.objects.get(id=request.user.id)
        if current_password and transaction_pin:
            message = change_transaction_pin_validate(
                self, user_profile.id, current_password, transaction_pin
            )
            if message == None:
                messages.success(request, "Successfully")
            else:
                messages.error(request, message)
        return redirect("/withdraw_password/")


class Team(LoginRequiredMixin, plan_income, View):
    login_url = "/login/"
    def get(self, request, *args):
        # if LastIncome.objects.filter(name="plan income").exists():
        #     last_income = LastIncome.objects.latest('id')
        #     time_diff = timezone.now() - last_income.last_paln_income
        #     if time_diff > timedelta(minutes=20):
        #         last_income.last_paln_income = timezone.now()
        #         plan_income_task1()
        #         LastIncome.update_lastincome(last_income.id)
        # else:
        #     last_income = LastIncome.objects.create(last_paln_income=timezone.now()).save()
        #     plan_income_task1()
        domainname = "prpinsurgent.com"
        user_wallet = wallet.objects.get(user=request.user.id)
        Level_1 = User.objects.filter(refer_parent=request.user)
        Level_2 = User.objects.filter(refer_parent__refer_parent=request.user)
        Level_3 = User.objects.filter(
            refer_parent__refer_parent__refer_parent=request.user
        )
        Level_1_count = User.objects.filter(refer_parent=request.user).count()
        Level_2_count = User.objects.filter(
            refer_parent__refer_parent=request.user
        ).count()
        Level_3_count = User.objects.filter(
            refer_parent__refer_parent__refer_parent=request.user
        ).count()
        total_income = (
            Level_1_income
        ) = Level_2_income = Level_3_income = total_cashback = 0
        Level_1_income_per_refer = []
        Level_2_income_per_refer = []
        Level_3_income_per_refer = []
        Level_1_name = []
        Level_2_name = []
        Level_3_name = []
        total_active_refer = []
        total_deposit_k = 0
        success_deposit = deposit.objects.filter(
            Q(user__refer_parent=request.user)
            | Q(user__refer_parent__refer_parent=request.user)
            | Q(user__refer_parent__refer_parent__refer_parent=request.user),
            status="Deposit Success",
        )

        level_1_deposit = user_plan.objects.filter(
            user__refer_parent=request.user,
            plan__price__gte=201,
        ).aggregate(level1_refer_deposit=(Sum("plan__price")))
        if level_1_deposit['level1_refer_deposit'] == None:
            level_1_deposit['level1_refer_deposit'] = 0

        level_2_deposit = user_plan.objects.filter(
            user__refer_parent__refer_parent=request.user,
            plan__price__gte=201,
        ).aggregate(level2_refer_deposit=(Sum("plan__price")))
        if level_2_deposit['level2_refer_deposit'] == None:
            level_2_deposit['level2_refer_deposit'] = 0
            
        level_3_deposit =  user_plan.objects.filter(
            user__refer_parent__refer_parent__refer_parent=request.user,
            plan__price__gte=201,
        ).aggregate(level3_refer_deposit=(Sum("plan__price")))
        if level_3_deposit['level3_refer_deposit'] == None:
            level_3_deposit['level3_refer_deposit'] = 0
        
        level_1_deposit_count = user_plan.objects.filter(
            user__refer_parent=request.user,
            plan__price__gte=201,
        ).count()

        level_2_deposit_count = user_plan.objects.filter(
            user__refer_parent__refer_parent=request.user,
            plan__price__gte=201,
        ).count()
   
        level_3_deposit_count =  user_plan.objects.filter(
            user__refer_parent__refer_parent__refer_parent=request.user,
            plan__price__gte=201,
        ).count()
        total_deposit_count = level_1_deposit_count + level_2_deposit_count + level_3_deposit_count
        total_deposit = float(level_1_deposit['level1_refer_deposit'] + level_2_deposit['level2_refer_deposit'] + level_3_deposit['level3_refer_deposit'] )
        # if total_deposit > 999:
        #     total_deposit_k = float(total_deposit)

        team_size = User.objects.filter(
            Q(refer_parent=request.user)
            | Q(refer_parent__refer_parent=request.user)
            | Q(refer_parent__refer_parent__refer_parent=request.user),
        ).count()
        for i in Level_1:
            total = 0
            for j in income.objects.filter(
                Q(income_resource="Reference Income")
                | Q(income_resource="Reference Join Income"),
                refer_user=i.id,
                user_level="Level 1",
            ):
                Level_1_income = float(Level_1_income + j.amount)
            #     total = 0
            #     for z in income.objects.filter(
            #         Q(income_resource="Reference Income")
            #         | Q(income_resource="Reference Join Income"),
            #         user_level="Level 1",
            #         refer_user=j.refer_user,
            #     ):
            #         total = total + z.amount
            # Level_1_income_per_refer.append(total)
            # Level_1_name.append(convert_middle_to_asterisk(int(i.phone_number)))
        for i in Level_2:
            total = 0
            for j in income.objects.filter(
                Q(income_resource="Reference Income")
                | Q(income_resource="Reference Join Income"),
                refer_user=i.id,
                user_level="Level 2",
            ):
                Level_2_income = float(Level_2_income + j.amount)
                # total = 0
            #     for z in income.objects.filter(
            #         Q(income_resource="Reference Income")
            #         | Q(income_resource="Reference Join Income"),
            #         refer_user=j.refer_user.id,
            #         user_level="Level 2",
            #     ):
            #         total = total + z.amount
            # Level_2_income_per_refer.append(total)
            # Level_2_name.append(convert_middle_to_asterisk(int(i.phone_number)))

        for i in Level_3:
            total = 0
            for j in income.objects.filter(
                Q(income_resource="Reference Income")
                |Q(income_resource="Reference CashBack")
                | Q(income_resource="Reference Join Income"),
                refer_user=i.id,
                user_level="Level 3",
            ):
                Level_3_income = float(Level_3_income + j.amount)
            #     total = 0
            #     for z in income.objects.filter(
            #         Q(income_resource="Reference Income")
            #         | Q(income_resource="Reference Join Income"),
            #         refer_user=j.refer_user.id,
            #         user_level="Level 3",
            #     ):
            #         total = total + z.amount
            # Level_3_income_per_refer.append(total)
            # Level_3_name.append(convert_middle_to_asterisk(int(i.phone_number)))

        total_refer_income = income.objects.filter(
            Q(income_resource="Reference Income")
            | Q(income_resource="Reference Join Income")
            | Q(income_resource="Reference CashBack"),
            user=request.user,
        )
        for i in total_refer_income:
            total_income = float(i.amount + total_income)

        total_refer_cashback = income.objects.filter(
            Q(income_resource="Reference Join Income")
            | Q(income_resource="Reference CashBack"),
            user=request.user,
        )

        for i in total_refer_cashback:
            total_cashback = float(i.amount + total_cashback)
            total_active_refer.append(i.refer_user)
        total_active_refer = len(set(total_active_refer))
        

        collect_task_reward = income.objects.filter(
            income_resource = "Task Completed",
            user=request.user,
        )

        Data = {
            "user_wallet": user_wallet,
            "Level_1_count": Level_1_count,
            "Level_2_count": Level_2_count,
            "Level_3_count": Level_3_count,
            "Level_1": Level_1,
            "Level_2": Level_2,
            "Level_3": Level_3,
            "Level_1_name": Level_1_name,
            "Level_2_name": Level_2_name,
            "Level_3_name": Level_3_name,
            "total_refer_income": total_refer_income,
            "team_size": team_size,
            "total_income": total_income,
            "level_1_deposit":level_1_deposit["level1_refer_deposit"],
            "level_2_deposit":level_2_deposit["level2_refer_deposit"],
            "level_3_deposit":level_3_deposit["level3_refer_deposit"],
            "total_refer_invest": total_deposit,
            "total_deposit_k": total_deposit_k,
            "Level_1_income": Level_1_income,
            "Level_2_income": Level_2_income,
            "Level_3_income": Level_3_income,
            "domainname": domainname,
            "total_cashback": total_cashback,
            "collect_task_reward": collect_task_reward,
            "level_1_deposit_count": level_1_deposit_count,
            "total_deposit_count":total_deposit_count,            
            "active_refer": total_active_refer,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "user_team.html", Data)


class Mine(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args):
        today = timezone.now().date()
        today1 = datetime.now().date()
        user_wallet = wallet.objects.get(user=request.user.id)
        daily_reward = income.objects.filter(
            Q(income_at__date=today)|
            Q(income_at__date=today1), 
            income_resource="Daily Reward", 
            user=request.user,
            ).exists()
        
        total_recharge = deposit.objects.filter(
            user=request.user,
            status="Deposit Success",
        ).aggregate(total_deposit=(Sum("amount")))
        if total_recharge["total_deposit"] == None:
            total_recharge["total_deposit"] = 0

        total_withdraw = withdraw.objects.filter(
            user=request.user,
            status="Withdraw Success",
        ).aggregate(total_cashout=(Sum("withdraw_amount")))
        if total_withdraw["total_cashout"] == None:
            total_withdraw["total_cashout"] = 0

        total_team_income = income.objects.filter(
            Q(income_resource="Reference Income")
            | Q(income_resource="Reference Join Income")
            | Q(income_resource="Reference CashBack"),
            user=request.user,
        ).aggregate(team_income=(Sum("amount")))
        if total_team_income['team_income'] == None:
            total_team_income['team_income'] = 0

        total_earning = income.objects.filter(
            user=request.user,
        ).aggregate(total_income=(Sum("amount")))
        if total_earning['total_income'] == None:
            total_earning['total_income'] = 0

        Data = {
            "user_wallet": user_wallet,
            'daily_reward': daily_reward,
            "total_recharge": total_recharge["total_deposit"],
            "total_withdraw": total_withdraw["total_cashout"],
            "total_team_income": total_team_income['team_income'],
            "total_earning": total_earning['total_income'],
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "Mine.html", Data)


class About_us(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args):
        user_wallet = wallet.objects.get(user=request.user.id)
        four_days_ago = timezone.now().date() - timedelta(days=4)
        Notifications = notification.objects.filter(
            user=request.user, created_at__gte=four_days_ago
        ).order_by("-created_at")
        new_notification = notification.objects.filter(
            user=request.user, is_open=False
        ).count()
        Data = {
            "user_wallet": user_wallet,
            "Notifications": Notifications,
            "new_notification": new_notification,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "about_us.html", Data)


class Our_services(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args):
        user_wallet = wallet.objects.get(user=request.user.id)
        Data = {
            "user_wallet": user_wallet,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        if whatsapp_group_link.objects.all():
            Whatsapp_link = whatsapp_group_link.objects.all().first()
            Data["Whatsapp_link"] = Whatsapp_link
        return render(request, "services.html", Data)


class ActivePlan(LoginRequiredMixin, View):
    login_url = "/login/"
    def get(self, request, *args):
        plans_days = []
        plans_days_progress = []
        income_per_plan = []
        total_user_income = 0
        total = 0
        user_wallet = wallet.objects.get(user=request.user.id)
        User_plans = user_plan.objects.filter(user__id=request.user.id).order_by("-id")
        total_income = income.objects.filter(
            user__id=request.user.id, income_resource="My Investment Income"
        )
        for j in total_income:
            total_user_income = total_user_income + j.amount
        total_user_income = round(total_user_income, 2)
        for i in User_plans:
            total_income = income.objects.filter(
                user__id=request.user.id,
                income_resource="My Investment Income",
                user_plan=user_plan.objects.get(id=i.id),
            )
            for j in total_income:
                total = float(total + j.amount)
            income_per_plan.append(total)
            total = 0
            if i.status == "In Process":
                time_diff = timezone.now() - i.started_at
                days_diff = int(time_diff.days + 1)
                days_diff_progress = ((days_diff - 1) * 100)/i.plan.plan_duration
                plans_days.append(days_diff)
                plans_days_progress.append(days_diff_progress)
            else:
                plans_days.append(i.plan.plan_duration)
                plans_days_progress.append(100)
        total_user_income = sum(income_per_plan)
        total_user_income = round(total_user_income, 2)
        User_plans_count = user_plan.objects.filter(
            user__id=request.user.id, status="In Process"
        ).count()

        Data = {
            "User_plans": User_plans,
            "user_wallet": user_wallet,
            "User_plans_count": User_plans_count,
            "total_user_income": total_user_income,
            "income_per_plan": income_per_plan,
            "plans_days": plans_days,
            "plans_days_progress": plans_days_progress,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "active_plans.html", Data)


class initial_popup(LoginRequiredMixin, View):
    login_url = "/login/"
    def get(self, request):
        # Check if the popup has already been shown
        if request.session.get("popup_shown", True):
            request.session["popup_shown"] = False
        return JsonResponse({"result": "show popup"})

class RewardCollect(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request):
       if not income.objects.filter(income_at__date=timezone.now().date(), income_resource="Daily Reward", user=request.user).exists():
          helper.daily_reward(request.user)
          print("result", "Reward Collected")
       else:
         print("Already Reward Collected")
       return redirect("/") 

    def post(self, request):
      if not income.objects.filter(income_at__date=timezone.now().date(), income_resource="Daily Reward", user=request.user).exists():
        helper.daily_reward(request.user)
        print(JsonResponse({"result": "Reward Collected"}))
        return JsonResponse({"result": "Reward Collected"})
      else:
        print(JsonResponse({"result": "Already Reward Collected"}))
        return JsonResponse({"result": "Already Reward Collected"})
 
class TaskCompleted(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, *args):
        user_wallet = wallet.objects.get(user=request.user.id)
        Level_1 = User.objects.filter(refer_parent=request.user)
        Level_1_count = User.objects.filter(refer_parent=request.user).count()
        Level_1_count_task_1 = (Level_1_count * 100)/15
        total_cashback = 0
        active_refer_task_2 = 0
        active_refer_task_3 = active_refer_task_4 = 0
        active_refer_task_5 = active_refer_task_6 = 0
        total_active_refer = []
        total_refer_cashback = income.objects.filter(
            income_resource="Reference CashBack",
            user=request.user,
        )
        for i in total_refer_cashback:
            total_cashback = float(i.amount + total_cashback)
            total_active_refer.append(i.refer_user)
        active_refer = len(set(total_active_refer))
        active_refer_task_2 = (active_refer * 100)/6
        if active_refer > 6:
           active_refer_task_3 = ((active_refer - 6) * 100)/10
        if active_refer > 16:
           active_refer_task_4 = ((active_refer - 16) * 100)/20
        if active_refer > 36:
           active_refer_task_5 = ((active_refer - 36) * 100)/30
        if active_refer > 66:
           active_refer_task_6 = ((active_refer - 66) * 100)/40

        collect_task_reward = income.objects.filter(
            income_resource = "Task Completed",
            user=request.user,
        )
        
        collect_task_one = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 15 friends to register and get 150 cash price",
            user=request.user,
        ).exists()
        collect_task_two = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 6 friends to singup and invest",
            user=request.user,
        ).exists()
        collect_task_three = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 10 friends to singup and invest",
            user=request.user,
        ).exists()
        collect_task_four = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 20 friends to singup and invest",
            user=request.user,
        ).exists()
        collect_task_five = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 30 friends to singup and invest",
            user=request.user,
        ).exists()
        collect_task_six = income.objects.filter(
            income_resource = "Task Completed",
            task_detail="Invite 40 friends to singup and invest",
            user=request.user,
        ).exists()

        level_1_deposit_count = deposit.objects.filter(
            user__refer_parent=request.user,
            status="Deposit Success",
        ).count()

        Data = {
            "user_wallet": user_wallet,
            "Level_1_count": Level_1_count,
            "Level_1_count_task_1": Level_1_count_task_1,
            "total_cashback": total_cashback,
            "collect_task_reward": collect_task_reward,
            "level_1_deposit_count": level_1_deposit_count,
            "active_refer": active_refer,
            "active_refer_task_2": active_refer_task_2,
            "active_refer_task_3": active_refer_task_3,
            "active_refer_task_4": active_refer_task_4,
            "active_refer_task_5": active_refer_task_5,
            "active_refer_task_6": active_refer_task_6,
            "collect_task_one":collect_task_one,
            "collect_task_two":collect_task_two,
            "collect_task_three": collect_task_three,
            "collect_task_four":collect_task_four,
            "collect_task_five":collect_task_five,
            "collect_task_six":collect_task_six,
        }
        if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data["Company_profile"] = Company_profile
        return render(request, "tasks.html", Data)


    def post(self, request):
        Data = request.POST
        amount = Data.get("amount", None)
        task_detail = Data.get("task_detail", None)
        message = helper.task_complete_income(request.user, amount, task_detail )
        if message == None:
             messages.success(request, "Task Reward Collected")
        else:
            messages.error(request, message)
        return redirect('/tasks/')

class Guide(LoginRequiredMixin, View):
       login_url='/login/'

       def get(self, request, *args):
          user_wallet = wallet.objects.get(user=request.user.id)
          Data = {'user_wallet': user_wallet}
          if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data['Company_profile'] = Company_profile
          return render(request, 'guide.html', Data)

class PostDepositSubmit(LoginRequiredMixin, View):
       login_url='/login/'

       def get(self, request, *args):
          user_wallet = wallet.objects.get(user=request.user.id)
          deposit_id = deposit.objects.filter(user=request.user).latest('id')
          Data = {'user_wallet': user_wallet, "deposit_id":deposit_id}
          if company_profile.objects.all():
            Company_profile = company_profile.objects.all().first()
            Data['Company_profile'] = Company_profile
          return render(request, 'one-pay-after-deposit.html', Data)