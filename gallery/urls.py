from django.urls import path
from gallery import views

urlpatterns = [
    path("test/", views.index, name="index"),
    path("", views.gallery, name="gallery"),
]
