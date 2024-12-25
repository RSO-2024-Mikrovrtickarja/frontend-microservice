from django.urls import path
from users import views

urlpatterns = [
    path("test/", views.index, name="index"),
    path("register/", views.registration, name="register"),
    path("login/", views.login, name="login")
]
