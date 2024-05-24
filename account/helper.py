from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
import random
from django.utils import timezone
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import (
    add_bank, bank_detail, 
    deposit, income, plan,
    user_plan, wallet, withdraw
    )

@receiver(post_save, sender=bank_detail) 
@receiver(post_save, sender=wallet) 
@receiver(post_save, sender=deposit) 
@receiver(post_save, sender=withdraw) 
@receiver(post_save, sender=user_plan) 
@receiver(post_save, sender=plan) 
def my_model_post_save(sender, instance, **kwargs):
    cache.clear()


def get_wallet_by_user(user):
    try:
        user_wallet = wallet.objects.get(user=user)
        return user_wallet
    except ObjectDoesNotExist as e:
        return False

def daily_reward(user):
    try:
    #   reward = random.randint(2, 9)
    #   if income.objects.filter(income_at__date=timezone.now().date(), income_resource="Daily Reward", user=request.user).exists():
    #       return None
      income.create_user_income(13, user, "Daily Reward")
      return None
    except ObjectDoesNotExist as e:
        message = "Internal server error"
        return message
    except Exception as e:
        message = e
        return message

def task_complete_income(user, amount, task_detail ):
    try:
      if income.objects.filter(user=user, income_resource="Task Completed", amount=amount).exists():
          message = "Already collected"
          return message
      income.create_user_income(int(amount), user, "Task Completed", None, None, None, task_detail=task_detail)
      return None
    except ObjectDoesNotExist as e:
        message = "Internal server error"
        return message
    except Exception as e:
        message = e
        return message

def bonus_income(user, amount, task_detail):
    try:
      income.create_user_income(int(amount), user, "Extra Bonus", None, None, None, task_detail=task_detail)
      return None
    except ObjectDoesNotExist as e:
        message = "Internal server error"
        return message
    except Exception as e:
        message = e
        return message

def get_user_plans(user):
    all_user_plan = user_plan.objects.filter(user=user)
    return all_user_plan


def get_user_process_plans(user):
    user_in_process_plans = user_plan.objects.filter(user=user, status="In Process")
    return user_in_process_plans


def get_user_Completed_plans(user):
    user_Completed_plans = user_plan.objects.filter(user=user, status="Completed")
    return user_Completed_plans


def update_bank_detail(account_title, account_number, bank_account_id, bank, bankname=None):
    try:
        Bank_detail = bank_detail.objects.get(id=bank_account_id)
        if bank == None:  
            bankname = add_bank.objects.get(bank_name__icontains=bankname)
        else:
            bankname = add_bank.objects.get(id=bank)
        Bank_detail.account_title = account_title
        Bank_detail.account_number = account_number
        Bank_detail.bank_id = bankname
        Bank_detail.save()
        return None
    except ObjectDoesNotExist as e:
        message = "Internal server error"
        return message
    except Exception as e:
        message = e
        return message


def update_plan_detail(
    plan_name,
    plan_price,
    total_income,
    duration,
    lanuch,
    quantity,
    id,
    plan_category,
    plan_level,
    image=None,
):
    try:
        Plan_detail = plan.objects.get(id=id)
        Plan_detail.name = plan_name
        Plan_detail.total_income = float(total_income)
        Plan_detail.price = float(plan_price)
        Plan_detail.plan_duration = int(duration)
        Plan_detail.is_launch = lanuch
        Plan_detail.plan_category = plan_category
        Plan_detail.quantity_limit = int(quantity)
        Plan_detail.plan_level = plan_level
        if image:
            Plan_detail.image = image
        Plan_detail.save()
        return None
    except ObjectDoesNotExist as e:
        message = e
        return message
    except Exception as e:
        message = e
        return message


def convert_middle_to_asterisk(number):
    number_str = str(number)
    length = len(number_str)

    if length <= 2:  # No middle part to replace
        return number

    middle_start = length // 2 - 2
    middle_end = middle_start + 4 if length % 2 == 0 else middle_start + 1

    modified_str = number_str[:middle_start] + "*" * (4) + number_str[7:]
    modified_number = modified_str
    return modified_number
