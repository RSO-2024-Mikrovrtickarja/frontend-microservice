from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegistrationForm, LoginForm
import requests
from .schemas import UserRegister, UserLogin, Token
from .settings import settings

# Create your views here.

USERS_HOST = settings.users_host
USERS_PORT = settings.users_port

def index(request):
    return HttpResponse("Hello, world.")

def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():

            user_registration_obj = UserRegister(username=request.POST["username"], email=request.POST["email"], password=request.POST["password1"])
            user_registration_url = f"http://{USERS_HOST}:{USERS_PORT}/register"

            user_registration_response = requests.post(user_registration_url, json=user_registration_obj.model_dump())

            if user_registration_response.status_code != 201:
                raise Exception(f"Failed to register new user. Returned status code: {user_registration_response.status_code}")

            return redirect("/login")
    else:
        form = RegistrationForm()

    return render(request, "registration.html", {"form":form})

def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            
            user_login_obj = UserLogin(username=request.POST["email"], password=request.POST["password"])
            user_login_url = f"http://{USERS_HOST}:{USERS_PORT}/login"

            user_login_response = requests.post(user_login_url, data=user_login_obj.model_dump())

            if user_login_response.status_code != 200:
                raise Exception(f"Failed to login. Returned status code: {user_login_response.status_code}")

            user_token = Token.model_validate(user_login_response.json())

            return redirect('/gallery')
    else:
        form = LoginForm()
    
    return render(request, "login.html", {"form":form})
