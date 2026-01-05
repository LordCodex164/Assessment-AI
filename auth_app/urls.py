from django.urls import path
from . import views

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="register_view"),
    path("login", views.LoginUserView.as_view(), name= "login_user_view"),
    path("", views.GetUserView.as_view(), name="get_user_view")
]