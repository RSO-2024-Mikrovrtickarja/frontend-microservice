from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("Hello, world.")

def gallery(request):

    return render(request, "gallery.html")

