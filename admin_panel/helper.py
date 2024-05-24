from django.core.exceptions import ObjectDoesNotExist

from account.models import deposit, plan, withdraw, bank_detail
from admin_panel.models import company_profile, whatsapp_group_link
from auths.models import User


def user_deactivate_activate(decision, id):
    try:
        user = User.objects.get(id=id)
        if decision == "deactivate":
            user.is_active = False
        elif decision == "activate":
            user.is_active = True
        user.save()
        return None
    except ObjectDoesNotExist as e:
        message = "User with this id is not found"
        return message


def plan_deactivate_activate(decision, id):
    try:
        Plan = plan.objects.get(id=id)
        if decision == "deactivate":
            Plan.is_launch = False
        elif decision == "lanuch":
            Plan.is_launch = True
        Plan.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Plan with this id is not found"
        return message

def plan_soft_delete(id):
    try:
        Plan = plan.objects.get(id=id)
        Plan.is_deleted = True
        Plan.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Plan with this id is not found"
        return message

def bank_account_soft_delete(id):
    try:
        Account = bank_detail.objects.get(id=id)
        Account.is_deleted = True
        Account.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Account with this id is not found"
        return message


def approve_reject_deposit(decision, id):
    try:
        Deposit = deposit.objects.get(id=id)
        if decision == "reject":
            Deposit.status = "Deposit Failed"
        elif decision == "approved":
            Deposit.status = "Deposit Success"
        Deposit.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Deposit request with this id is not found"
        return message


def approve_reject_withdraw(decision, id):
    try:
        Withdraw = withdraw.objects.get(id=id)
        if decision == "reject":
            Withdraw.status = "Withdraw Failed"
        elif decision == "approved":
            Withdraw.status = "Withdraw Success"
        Withdraw.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Withdraw request with this id is not found"
        return message


def update_company_profile(company_name, company_logo, company_address, id):
    try:
        Company_profile = company_profile.objects.get(id=id)
        if company_name and company_address:
            Company_profile.company_name = company_name
            Company_profile.company_address = company_address
            Company_profile.save()
        elif company_logo != None:
            Company_profile.company_logo = company_logo
            Company_profile.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Company with this id is not found"
        return message


def update_social_media_link(join_link,telegram_link, phone_number, id):
    try:
        update_group_link = whatsapp_group_link.objects.get(id=id)
        if join_link:
            update_group_link.join_link = join_link
            update_group_link.telegram_link = telegram_link
            update_group_link.phone_number = phone_number
            update_group_link.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Whatsapp link with this id is not found"
        return message
