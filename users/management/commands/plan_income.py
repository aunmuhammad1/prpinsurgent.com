import threading
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from account.models import income, user_plan, wallet


def plan_income_task():
    current_time = datetime.now().time()
    # current_hour = current_time.hour
    #  if current_hour >= 2 and current_hour < 3:
    user_plans = user_plan.objects.filter(status="In Process")
    for i in user_plans:
        plan_start_time = i.started_at
        plan_end_time = i.completed_at
        time_diff = timezone.now() - plan_start_time
        if time_diff > timedelta(minutes=60):
            try:
                latest_income = income.objects.filter(
                    user=i.user, user_plan=user_plan.objects.get(id=i.id)
                ).latest("income_at")
                time_diff = timezone.now() - latest_income.income_at
                if time_diff > timedelta(minutes=59):
                    income.create_user_income(
                        i.plan.hourly_income,
                        i.user,
                        "My Investment Income",
                        user_plan=user_plan.objects.get(id=i.id),
                    )
                    if i.user.refer_parent and int(i.plan.price) > 200:
                        refer_level_1 = i.user.refer_parent
                        amount = i.plan.hourly_income * (10 / 100)
                        income.create_user_income(
                            amount,
                            refer_level_1,
                            "Reference Income",
                            None,
                            i.user,
                            "Level 1",
                        )
                        if refer_level_1.refer_parent:
                            amount = i.plan.hourly_income * (5 / 100)
                            refer_level_2 = refer_level_1.refer_parent
                            income.create_user_income(
                                amount,
                                refer_level_2,
                                "Reference Income",
                                None,
                                refer_level_1.refer_parent,
                                "Level 2",
                            )
                            if refer_level_2.refer_parent:
                                amount = i.plan.hourly_income * (1 / 100)
                                refer_level_3 = refer_level_2.refer_parent
                                income.create_user_income(
                                    amount,
                                    refer_level_3,
                                    "Reference Income",
                                    None,
                                    refer_level_2.refer_parent,
                                    "Level 3",
                                )
            except ObjectDoesNotExist as e:
                latest_income = False
                income.create_user_income(
                    i.plan.hourly_income,
                    i.user,
                    "My Investment Income",
                    user_plan=user_plan.objects.get(id=i.id),
                )

                if i.user.refer_parent and int(i.plan.price) > 200:
                    refer_level_1 = i.user.refer_parent
                    amount = i.plan.hourly_income * (10 / 100)
                    income.create_user_income(
                        amount,
                        refer_level_1,
                        "Reference Income",
                        None,
                        i.user,
                        "Level 1",
                    )
                    if refer_level_1.refer_parent:
                        amount = i.plan.hourly_income * (5 / 100)
                        refer_level_2 = refer_level_1.refer_parent
                        income.create_user_income(
                            amount,
                            refer_level_2,
                            "Reference Income",
                            None,
                            i.user,
                            "Level 2",
                        )
                        if refer_level_2.refer_parent:
                            amount = i.plan.hourly_income * (1 / 100)
                            refer_level_3 = refer_level_2.refer_parent
                            income.create_user_income(
                                amount,
                                refer_level_3,
                                "Reference Income",
                                None,
                                i.user,
                                "Level 3",
                            )
                            
        if plan_end_time < timezone.now():
            user_plans_complete = user_plan.objects.get(id=i.id)
            user_plans_complete.status = "Completed"
            user_plans_complete.save()
    threading.Timer(20 * 60, plan_income_task).start()

def plan_income_task1():
    user_plans = user_plan.objects.filter(status="In Process")
    for i in user_plans:
        plan_start_time = i.started_at
        plan_end_time = i.completed_at
        time_diff = timezone.now() - plan_start_time
        if time_diff > timedelta(minutes=60):
            try:
                latest_income = income.objects.filter(
                    user=i.user, user_plan=user_plan.objects.get(id=i.id)
                ).latest("income_at")
                time_diff = timezone.now() - latest_income.income_at
                if time_diff > timedelta(minutes=59):
                    income.create_user_income(
                        i.plan.hourly_income,
                        i.user,
                        "My Investment Income",
                        user_plan=user_plan.objects.get(id=i.id),
                    )
                    if i.user.refer_parent and int(i.plan.price) > 200:
                        refer_level_1 = i.user.refer_parent
                        amount = i.plan.hourly_income * (10 / 100)
                        income.create_user_income(
                            amount,
                            refer_level_1,
                            "Reference Income",
                            None,
                            i.user,
                            "Level 1",
                        )
                        if refer_level_1.refer_parent:
                            amount = i.plan.hourly_income * (5 / 100)
                            refer_level_2 = refer_level_1.refer_parent
                            income.create_user_income(
                                amount,
                                refer_level_2,
                                "Reference Income",
                                None,
                                refer_level_1.refer_parent,
                                "Level 2",
                            )
                            if refer_level_2.refer_parent:
                                amount = i.plan.hourly_income * (1 / 100)
                                refer_level_3 = refer_level_2.refer_parent
                                income.create_user_income(
                                    amount,
                                    refer_level_3,
                                    "Reference Income",
                                    None,
                                    refer_level_2.refer_parent,
                                    "Level 3",
                                )
            except ObjectDoesNotExist as e:
                latest_income = False
                income.create_user_income(
                    i.plan.hourly_income,
                    i.user,
                    "My Investment Income",
                    user_plan=user_plan.objects.get(id=i.id),
                )

                if i.user.refer_parent and int(i.plan.price) > 200:
                    refer_level_1 = i.user.refer_parent
                    amount = i.plan.hourly_income * (10 / 100)
                    income.create_user_income(
                        amount,
                        refer_level_1,
                        "Reference Income",
                        None,
                        i.user,
                        "Level 1",
                    )
                    if refer_level_1.refer_parent:
                        amount = i.plan.hourly_income * (5 / 100)
                        refer_level_2 = refer_level_1.refer_parent
                        income.create_user_income(
                            amount,
                            refer_level_2,
                            "Reference Income",
                            None,
                            i.user,
                            "Level 2",
                        )
                        if refer_level_2.refer_parent:
                            amount = i.plan.hourly_income * (1 / 100)
                            refer_level_3 = refer_level_2.refer_parent
                            income.create_user_income(
                                amount,
                                refer_level_3,
                                "Reference Income",
                                None,
                                i.user,
                                "Level 3",
                            )
                            
        if plan_end_time < timezone.now():
            user_plans_complete = user_plan.objects.get(id=i.id)
            user_plans_complete.status = "Completed"
            user_plans_complete.save()
    
class Command(BaseCommand):
    help = "Starts the auto add task"

    def handle(self, *args, **options):
        # Start the periodic task
        plan_income_task()
