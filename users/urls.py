from django.urls import path

from users import views

urlpatterns = [
    path("", views.Home.as_view(), name="user_home_page"),
    path("account/", views.Bank_amount_setting.as_view(), name="bank_account_page"),
    path("plans/", views.Invest.as_view(), name="user_inest_plans"),
    path("recharge/", views.Recharge.as_view(), name="recharge_page"),
    path("withdraw/", views.Withdraw_amount.as_view(), name="withdraw_page"),
    path("income/", views.MyBills.as_view(), name="bill_history"),
    path("withdraw_history/", views.WithdrawHistory.as_view(), name="WithdrawHistory"),
    path("withdraw_password/", views.WithdrawPassword.as_view(), name="withdraw_password"),
    path("deposit_history/", views.DepositHistory.as_view(), name="My_deposit_history"),
    path("user_profile/", views.Profile.as_view(), name="User_profile_page"),
    path("myteam/", views.Team.as_view(), name="user_reference_team"),
    path("mine/", views.Mine.as_view(), name="about_us_page"),
    path("about_us/", views.About_us.as_view(), name="about_us_page"),
    path("services/", views.Our_services.as_view(), name="Our_services"),
    path("popup/intial/", views.initial_popup.as_view()),
    path("popup/dailyreward/",views.RewardCollect.as_view()),
    path("activePlan/", views.ActivePlan.as_view(), name="MyProject"),
    path("plan_thread/", views.plan_income.as_view()),
    path('task_completed/', views.TaskCompleted.as_view(), name="task_completed"),
    path("tasks/", views.TaskCompleted.as_view(), name="tasks"),
    path('income_guide/', views.Guide.as_view(), name='guide'),
    path('onepayPostDeposit/', views.PostDepositSubmit.as_view(), name="PostDepositSubmit"),

]
