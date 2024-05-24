import sys
import uuid
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils import timezone

from auths.image_processing import generate_thumbnail
from auths.models import User
from users.models import notification

# Create your models here.


class wallet(models.Model):
    class Meta:
        db_table = "wallet"
        verbose_name_plural = "wallets"
        managed = True
        ordering = ["-created_at"]

    balance = models.FloatField(default=200)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, unique=True, related_name="user_wallet"
    )
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def create_user_wallet(user):
        add_wallet = wallet(user=user).save()
        return add_wallet

    def __str__(self):
        return self.user.username


class plan(models.Model):
    class Meta:
        db_table = "plan"
        verbose_name_plural = "plans"
        managed = True
        ordering = ["-id"]

    TYPE = (
        ("Simple Plan", "Simple Plan"),
        ("VIP Plan", "VIP Plan"),
    )
    name = models.CharField(max_length=180, null=False, blank=False, unique=True)
    plan_level = models.CharField(max_length=50, default='1')
    plan_category = models.CharField(
        max_length=100, choices=TYPE, default="Simple Plan"
    )
    image = models.ImageField(upload_to="plan_images/", null=True, blank=True)
    price = models.PositiveBigIntegerField()
    plan_duration = models.PositiveIntegerField()
    total_income = models.FloatField()
    daily_income = models.FloatField()
    hourly_income = models.FloatField()
    quantity_limit = models.IntegerField(default=1)
    is_launch = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)


    def create_new_plan(
        plan_name,
        plan_price,
        total_income,
        duration,
        lanuch,
        quantity,
        image=None,
        plan_level=1,
        plan_category=None,
    ):
        try:
            if plan.objects.filter(name=plan_name):
                message = "Plan with this name is already exit"
                return message
            plan(
                name=plan_name,
                price=float(plan_price),
                plan_duration=int(duration),
                total_income=float(total_income),
                quantity_limit=int(quantity),
                is_launch=lanuch,
                plan_level=plan_level,
                plan_category=plan_category,
                image=image,
            ).save()
            return None
        except Exception as e:
            message = e
            return message

    def delete(self, using=None, keep_parents=False):
        self.image.storage.delete(self.image.name)
        super().delete()

    def save(self, *args, **kwargs):
        self.daily_income = self.total_income / self.plan_duration
        self.daily_income = round(self.daily_income, 2)
        self.hourly_income = self.total_income / (self.plan_duration * 24)
        self.hourly_income = round(self.hourly_income, 2)
        if self.image and not self.id:
            output = generate_thumbnail(self.image, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
        if self.image and self.id:
            old_data = plan.objects.get(id=self.id)
            output = generate_thumbnail(self.image, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
            if old_data.image.name:
                old_data.image.storage.delete(old_data.image.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class user_plan(models.Model):
    class Meta:
        db_table = "user_plan"
        verbose_name_plural = "user_plans"
        managed = True
        ordering = ["-id"]

    STATUS = (
        ("In Process", "In Process"),
        ("Completed", "Completed"),
    )
    plan = models.ForeignKey(plan, on_delete=models.CASCADE, related_name="buy_plan")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_plan")
    status = models.CharField(max_length=100, choices=STATUS, default="In Process")
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.started_at = timezone.now()
            self.completed_at = self.started_at + timedelta(
                days=self.plan.plan_duration
            )
            user_wallet = wallet.objects.get(user=self.user)
            user_wallet.balance = user_wallet.balance - self.plan.price
            user_wallet.updated_at = timezone.now()
            user_wallet.save()
            if self.user.refer_parent and int(self.plan.price) > 200:
                refer_level_1 = User.objects.get(
                    refer_code=self.user.refer_parent.refer_code
                )

                amount = self.plan.price * (18 / 100)
                income.create_user_income(
                        amount,
                        refer_level_1,
                        "Reference CashBack",
                        None,
                        self.user,
                        "Level 1",
                )
                # if refer_level_1.refer_parent:
                #     amount = self.plan.price * (3 / 100)
                #     refer_level_2 = refer_level_1.refer_parent
                #     income.create_user_income(
                #         amount,
                #         refer_level_2,
                #         "Reference CashBack",
                #         None,
                #         refer_level_1.refer_parent,
                #         "Level 2",
                #     )
                #     if refer_level_2.refer_parent:
                #         amount = self.plan.price * (1 / 100)
                #         refer_level_3 = refer_level_2.refer_parent
                #         income.create_user_income(
                #         amount,
                #         refer_level_3,
                #         "Reference CashBack",
                #         None,
                #         refer_level_2.refer_parent,
                #         "Level 3",
                #         )
                # else:
                #     amount = self.plan.price * (25 / 100)
                #     income.create_user_income(
                #         amount,
                #         refer_level_1,
                #         "Reference CashBack",
                #         None,
                #         self.user,
                #         "Level 1",
                #     )
                # if refer_level_1.refer_parent:
                #     amount = self.plan.price * (5 / 100)
                #     refer_level_2 = User.objects.get(
                #         refer_code=refer_level_1.refer_parent.refer_code
                #     )
                #     income.create_user_income(
                #         amount,
                #         refer_level_2,
                #         "Reference Income",
                #         None,
                #         self.user,
                #         "Level 2",
                #     )
                #     if refer_level_2.refer_parent:
                #         amount = self.plan.price * (1 / 100)
                #         refer_level_3 = User.objects.get(
                #             refer_code=refer_level_2.refer_parent.refer_code
                #         )
                #         income.create_user_income(
                #             amount,
                #             refer_level_3,
                #             "Reference Income",
                #             None,
                #             self.user,
                #             "Level 3",
                #         )

        super().save(*args, **kwargs)

    def create_user_plan(buy_plan, user):
        try:
            Wallet = wallet.objects.get(user=user)
            user = User.objects.get(id=user)
            Plan_price = plan.objects.get(name=buy_plan)
            if Wallet.balance < Plan_price.price:
                message = "Your Wallet have insufficient balance to buy this plan "
                return message
            user_plan(plan=Plan_price, user=user).save()
            return None
        except ObjectDoesNotExist as e:
            message = "Selected plan is not found"
            return message
        except Exception as e:
            message = e
            return message

    def __str__(self):
        return self.plan.name


class deposit_image(models.Model):
    class Meta:
        db_table = "deposit_image"
        verbose_name_plural = "deposit_images"
        managed = True
        ordering = ["-id"]

    image = models.ImageField(upload_to="deposit_images/")

    def save(self, *args, **kwargs):
        if not self.id:
            output = generate_thumbnail(self.image, 1024, 768)
            name = "%s.jpg" % str(uuid.uuid4())
            self.image = InMemoryUploadedFile(
                output, "ImageField", name, "image/jpeg", sys.getsizeof(output), None
            )
            super().save(*args, **kwargs)


class deposit(models.Model):
    class Meta:
        db_table = "deposit"
        verbose_name_plural = "deposits"
        managed = True
        ordering = ["-id"]

    STATUS = (
        ("Pending", "Pending"),
        ("Deposit Failed", "Deposit Failed"),
        ("Deposit Success", "Deposit Success"),
    )
    amount = models.PositiveBigIntegerField(default=0)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="deposit_request_user",
        null=True,
        blank=True,
    )
    images = models.ManyToManyField(deposit_image, blank=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS, default="Pending")
    deposit_request_at = models.DateTimeField(auto_now_add=True)
    approved_or_rejected_at = models.DateTimeField(blank=True, null=True)

    def create_deposit_request(amount, user, image):
        try:
            user_id = User.objects.get(id=user)
            deposit(amount=amount, user=user_id).save()
            deposit_request = deposit.objects.latest("id")
            for j in image:
                deposit_image(image=j).save()
                deposit_request.images.add(deposit_image.objects.latest("id"))
            deposit_request.images.save()
            return None
        except Exception as e:
            message = "Internal server error"
            return message

    def save(self, *args, **kwargs):
        if not self.id and self.status == "Pending":
            from account.helper import convert_middle_to_asterisk

            admin_user = User.objects.filter(is_superuser=True).first()
            converted_str = convert_middle_to_asterisk(int(self.user.phone_number))
            notification.create_user_notification(
                admin_user,
                "Recharge Request",
                str(
                    "New Recharge request Rs "
                    + str(self.amount)
                    + " form user "
                    + str(converted_str)
                    + "."
                ),
            )
        if self.id and self.approved_or_rejected_at:
            old_data = deposit.objects.get(id=self.id)
            if (
                old_data.status == "Deposit Failed" or old_data.status == "Pending"
            ) and self.status == "Deposit Success":
                user_wallet = wallet.objects.get(user=self.user)
                user_wallet.balance = user_wallet.balance + self.amount
                user_wallet.updated_at = timezone.now()
                user_wallet.save()
                notification.create_user_notification(
                    self.user,
                    "Recharge Success",
                    str(
                        "Your Recharge request Rs "
                        + str(self.amount)
                        + " approved after review"
                    ),
                )
                self.approved_or_rejected_at = timezone.now()

        if self.status == "Deposit Success" and self.approved_or_rejected_at is None:
            user_wallet = wallet.objects.get(user=self.user)
            user_wallet.balance = user_wallet.balance + self.amount
            user_wallet.updated_at = timezone.now()
            user_wallet.save()
            self.approved_or_rejected_at = timezone.now()
            notification.create_user_notification(
                self.user,
                "Recharge Success",
                str("Your Recharge request Rs " + str(self.amount) + " approved "),
            )

        elif self.status == "Deposit Failed" and self.approved_or_rejected_at is None:
            self.approved_or_rejected_at = timezone.now()
            notification.create_user_notification(
                self.user,
                "Recharge Failed",
                str("Your Recharge request Rs " + str(self.amount) + " Rejected"),
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class add_bank(models.Model):
    class Meta:
        db_table = "add_bank"
        verbose_name_plural = "add_banks"
        managed = True
        ordering = ["-id"]

    bank_name = models.CharField(max_length=200, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def create__new_bank(bank_name):
        try:
            add_bank(bank_name=bank_name).save()
            return None
        except Exception as e:
            message = "Internal server error"
            return message

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.bank_name


class bank_detail(models.Model):
    class Meta:
        db_table = "bank_detail"
        verbose_name_plural = "bank_details"
        managed = True
        ordering = ["-id"]

    Method = (
        ("Easypasia", "Easypasia"),
        ("JazzCash", "JazzCash"),
    )
    account_title = models.CharField(max_length=150, null=False, blank=False)
    account_number = models.PositiveBigIntegerField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_bank_detail",
        null=True,
        blank=True,
    )
    # bank = models.CharField(max_length=100, choices=Method)
    bank_id = models.ForeignKey(
        add_bank, on_delete=models.PROTECT, null=True, blank=True
    )
    is_deleted = models.BooleanField(default=False)

    def create_bank_detail(account_title, account_number, user, bank, bankname=None):
        try:
            if bank == None:  
                bankname = add_bank.objects.get(bank_name__icontains=bankname)
            else:
              bankname = add_bank.objects.get(id=bank)
            bank_detail(
                account_title=account_title,
                account_number=account_number,
                user=user,
                bank_id=bankname,
            ).save()
            return None
        except Exception as e:
            message = "Internal server error"
            return message

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.account_title


class withdraw(models.Model):
    class Meta:
        db_table = "withdraw"
        verbose_name_plural = "withdraws"
        managed = True
        ordering = ["-id"]

    STATUS = (
        ("Pending", "Pending"),
        ("Withdraw Failed", "Withdraw Failed"),
        ("Withdraw Success", "Withdraw Success"),
    )
    withdraw_amount = models.FloatField(default=0)
    amount_received = models.FloatField()
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="withdraw_request_user"
    )
    user_account = models.ForeignKey(
        bank_detail, on_delete=models.CASCADE, related_name="user_account"
    )
    status = models.CharField(max_length=100, choices=STATUS, default="Pending")
    withdraw_request_at = models.DateTimeField(auto_now_add=True)
    approved_or_rejected_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def create_withdraw_request(amount, user, account):
        try:
            if wallet.objects.filter(user=user):
                user_wallet = wallet.objects.get(user=user)
                Bank_account = bank_detail.objects.get(id=account)
                if amount > user_wallet.balance:
                    message = "insufficient balance"
                    return message
                withdraw(
                    withdraw_amount=amount, user=user, user_account=Bank_account
                ).save()
                return None
        except ObjectDoesNotExist:
            message = "You have insufficient balance"
            return message
        except Exception as e:
            message = "Internal server error"
            return message

    def save(self, *args, **kwargs):
        if not self.id:
            self.amount_received = self.withdraw_amount * (88 / 100)
        if self.status == "Withdraw Success" and self.approved_or_rejected_at is None:
            self.approved_or_rejected_at = timezone.now()
            notification.create_user_notification(
                self.user,
                "Withdraw Success",
                str(
                    "Your withdraw request Rs "
                    + str(self.withdraw_amount)
                    + " apprived"
                ),
            )
        elif self.status == "Withdraw Success" and not self.id:
            self.approved_or_rejected_at = timezone.now()
            notification.create_user_notification(
                self.user,
                "Withdraw Success",
                "Your withdraw request Rs " + str(self.withdraw_amount) + " apprived",
            )
        elif self.status == "Withdraw Failed" and self.approved_or_rejected_at is None:
            user_wallet = wallet.objects.get(user=self.user)
            user_wallet.balance = user_wallet.balance + self.withdraw_amount
            user_wallet.updated_at = timezone.now()
            user_wallet.save()
            self.approved_or_rejected_at = timezone.now()
            notification.create_user_notification(
                self.user,
                "Withdraw Failed",
                "Your withdraw request Rs " + str(self.withdraw_amount) + " Rejected",
            )
        elif self.status == "Pending" and not self.id:
            from account.helper import convert_middle_to_asterisk

            user_wallet = wallet.objects.get(user=self.user)
            user_wallet.balance = user_wallet.balance - self.withdraw_amount
            user_wallet.updated_at = timezone.now()
            user_wallet.save()
            admin_user = User.objects.filter(is_superuser=True).first()
            converted_str = convert_middle_to_asterisk(int(self.user.phone_number))
            notification.create_user_notification(
                admin_user,
                "Withdraw Request",
                "New withdraw request Rs "
                + str(self.withdraw_amount)
                + " form user "
                + str(converted_str)
                + ".",
            )
        if self.id and self.approved_or_rejected_at:
            old_data = withdraw.objects.get(id=self.id)
            if (
                old_data.status == "Withdraw Failed"
            ) and self.status == "Withdraw Success":
                user_wallet = wallet.objects.get(user=self.user)
                user_wallet.balance = user_wallet.balance - self.withdraw_amount
                user_wallet.updated_at = timezone.now()
                user_wallet.save()
                notification.create_user_notification(
                    self.user,
                    "Withdraw Success",
                    "Your withdraw request Rs "
                    + str(self.withdraw_amount)
                    + " apprived after revuew",
                )
            elif (
                old_data.status == "Withdraw Success"
            ) and self.status == "Withdraw Failed":
                user_wallet = wallet.objects.get(user=self.user)
                user_wallet.balance = user_wallet.balance + self.withdraw_amount
                user_wallet.updated_at = timezone.now()
                user_wallet.save()
                notification.create_user_notification(
                    self.user,
                    "Withdraw Failed",
                    "Your withdraw request Rs "
                    + str(self.withdraw_amount)
                    + " Rejected after revuew",
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class income(models.Model):
    class Meta:
        db_table = "income"
        verbose_name_plural = "incomes"
        managed = True
        ordering = ["-id"]

    Income_resource = (
        ("My Investment Income", "My Investment Income"),
        ("Reference Income", "Reference Income"),
        ("Reference CashBack", "Reference CashBack"),
        ("Reference Join Income", "Reference Join Income"),
        ("Daily Reward", "Daily Reward"),
        ("Task Completed", "Task Completed"),
        ("Extra Bonus", "Extra Bonus"),
    )
    REFER_LEVEL = (
        ("Level 1", "Level 1"),
        ("Level 2", "Level 2"),
        ("Level 3", "Level 3"),
    )
    amount = models.FloatField(null=False, blank=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user", null=True, blank=True
    )
    refer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="from_user", null=True, blank=True
    )
    user_level = models.CharField(
        max_length=100, null=True, blank=True, choices=REFER_LEVEL
    )
    income_resource = models.CharField(max_length=100, choices=Income_resource)
    user_plan = models.ForeignKey(
        user_plan,
        null=True,
        blank=True,
        related_name="resource_plan",
        on_delete=models.CASCADE,
    )
    income_at = models.DateTimeField(auto_now_add=True)
    task_detail = models.CharField(null=True, blank=True, max_length=100)

    def create_user_income(
        amount, user, resource, user_plan=None, refer_user=None, user_level=None, task_detail=None
    ):
        add_income = income(
            amount=amount,
            user=user,
            income_resource=resource,
            user_plan=user_plan,
            refer_user=refer_user,
            user_level=user_level,
            task_detail=task_detail,
        )
        return add_income.save()

    def save(self, *args, **kwargs):
        if not self.id:
            try:
                user_wallet = wallet.objects.get(user=self.user)
                user_wallet.balance = user_wallet.balance + self.amount
                user_wallet.updated_at = timezone.now()
                user_wallet.save()
            except ObjectDoesNotExist as e:
                message = "Request User Wallet Not Found"
                return message
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

class LastIncome(models.Model):
    name = models.CharField(max_length=50,  blank=True, default="plan income")
    last_paln_income = models.DateTimeField()

    def __str__(self):
        return self.name

    def update_lastincome(id):
        latestincome = LastIncome.objects.get(id=id)
        latestincome.last_paln_income = timezone.now()
        latestincome.save()
        return latestincome

class votes(models.Model):
    class Meta:
        db_table = "vote"
        verbose_name_plural = "votes"
        managed = True
        ordering = ["-id"]
        unique_together = ["plan", "user"]


    Decision = (
        ("Yes", "Yes"),
        ("No", "No"),
    )

    plan = models.ForeignKey(plan, on_delete=models.CASCADE, related_name="plan_vote")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="user_vote")
    vote = models.CharField(max_length=100, choices=Decision)
    vote_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.vote