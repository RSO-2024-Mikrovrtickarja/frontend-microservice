from django.urls import path
from gallery import views

urlpatterns = [
    path("test/", views.index, name="index"),
    path("", views.gallery, name="gallery"),
    path("image/view/<slug:slug>", views.view_image, name='view image'),
    path("image/download/<slug:slug>", views.download_image, name='download image'),
    path("image/share/<slug:slug>", views.share_image, name='share image'),
    path("image/delete/<slug:slug>", views.delete_image, name='delete image'),
    path("image/upload", views.upload_image, name='upload image'),
    path("image/convert/<slug:slug>", views.convert_image, name='convert image')
    
]
