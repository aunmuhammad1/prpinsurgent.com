from django.contrib.auth.views import LogoutView
from django.urls import path

from auths import views

urlpatterns = [
    path("", views.Login.as_view(), name="user_Login"),
    # path("forgetpassword/", views.Forgetpassword.as_view(), name="forgetpassword_Form"),
    # path("changePassword/", views.Changepassword.as_view(), name="changePassword"),
    path("signup/", views.Sign_Up.as_view(), name="register_new_user"),
    # path(
    #     "signup/<str:refer_code>/",
    #     views.Sign_Up.as_view(),
    #     name="register_with_reference",
    # ),
    path("logout/", LogoutView.as_view(next_page="/login/"), name="Logout"),
]
