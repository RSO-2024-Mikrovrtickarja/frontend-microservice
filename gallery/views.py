
from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests

import frontend.settings
from .models import PublicImage, InternalImage, PublicImageProcessingJobRequest
from frontend.config import config
import os
from PIL import Image
from tempfile import SpooledTemporaryFile
import base64

# Create your views here.

PHOTO_STORAGE_HOST = config.photo_storage_host
PHOTO_STORAGE_PORT = config.photo_storage_port

def index(request):
    return HttpResponse("Hello, world.")

def download_image_request(image_id: str, user_token: str) -> requests.Response:
    download_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{image_id}/download"
    download_image_response = requests.get(download_image_url, headers={"Authorization": user_token})

    if download_image_response.status_code != 200:
        raise Exception(f"Failed to download image {image_id}. Returned status code: {download_image_response.status_code}")
    return download_image_response

def gallery(request):
    
    user_token = request.COOKIES.get('jwt')
    
    if not user_token:
         return redirect("/users/login")

    get_all_images_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images"
    get_all_images_response = requests.get(get_all_images_url, headers={"Authorization": user_token})

    if get_all_images_response.status_code != 200:
        raise Exception(f"Failed to get all images. Returned status code: {get_all_images_response.status_code}")

    all_images_internal = {"images": []}
    for image in get_all_images_response.json()["images"]:
        public_image_obj = PublicImage.model_validate(image)

        image_id = str(public_image_obj.id)
        image_data = base64.b64encode(download_image_request(image_id, user_token).content).decode('ascii')
        intermediate_image_buffer = SpooledTemporaryFile(mode="w+b")
        intermediate_image_buffer.write(download_image_request(image_id, user_token).content)
        intermediate_image_buffer.seek(0, os.SEEK_SET)

        with Image.open(intermediate_image_buffer) as img_obj:
            img_id = image_id
            name = public_image_obj.file_name
            file_format = img_obj.format
            width = img_obj.width
            height = img_obj.height
            uploaded_at = public_image_obj.uploaded_at.strftime("%d.%m.%Y %H:%M")
            internal_image_obj = InternalImage(id=img_id,
                                               file_name=name, 
                                               file_format=file_format, 
                                               width=width, 
                                               height=height,
                                               uploaded_at=uploaded_at,
                                               data=image_data)
            all_images_internal["images"].append(internal_image_obj.model_dump())
            intermediate_image_buffer.close()
        
    context = all_images_internal
    
    return render(request, "gallery.html", context)

def view_image(request, slug):
    user_token = request.COOKIES.get('jwt')

    get_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}"
    get_image_response = requests.get(get_image_url, headers={"Authorization": user_token})

    if get_image_response.status_code != 200:
        raise Exception(f"Failed to get image {slug}. Returned status code: {get_image_response.status_code}")
    
    image_public = get_image_response.json()
    image_internal = {"image": []}
    
    public_image_obj = PublicImage.model_validate(image_public["image"])
    
    image_data = base64.b64encode(download_image_request(slug, user_token).content).decode('ascii')
    intermediate_image_buffer = SpooledTemporaryFile(mode="w+b")
    intermediate_image_buffer.write(download_image_request(slug, user_token).content)
    intermediate_image_buffer.seek(0, os.SEEK_SET)

    with Image.open(intermediate_image_buffer) as img_obj:
        img_id = str(public_image_obj.id)
        name = public_image_obj.file_name
        file_format = img_obj.format
        width = img_obj.width
        height = img_obj.height
        uploaded_at = public_image_obj.uploaded_at.strftime("%d.%m.%Y %H:%M")
        internal_image_obj = InternalImage(id=img_id,
                                           file_name=name,
                                           file_format=file_format,
                                           width=width,
                                           height=height,
                                           uploaded_at=uploaded_at,
                                           data=image_data)

        image_internal["image"] = internal_image_obj.model_dump()

    context = image_internal

    return render(request, "image.html", context)

def download_image(request, slug):
    user_token = request.COOKIES.get('jwt')
    download_image_response = download_image_request(slug, user_token)
    
    response = HttpResponse(download_image_response.content, content_type=download_image_response.headers["content-type"])
    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(download_image_response.headers["Content-Disposition"])
    
    return response

def share_image(request, slug):
    user_token = request.COOKIES.get('jwt')
    
    # TODO
    
    return redirect("/gallery")

def delete_image(request, slug):
    user_token = request.COOKIES.get('jwt')

    delete_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}"
    delete_image_response = requests.delete(delete_image_url, headers={"Authorization": user_token})

    if delete_image_response.status_code != 200:
        raise Exception(f"Failed to delete image {slug}. Returned status code: {delete_image_response.status_code}")
    
    return redirect("/gallery")

def upload_image(request):
    user_token = request.COOKIES.get('jwt')
    
    if request.method == "POST" and request.FILES["image"]:
        image = {"uploaded_file": request.FILES["image"]}

        upload_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images"
        upload_image_response = requests.post(upload_image_url, files=image, headers={"Authorization": user_token})

        if upload_image_response.status_code != 200:
            raise Exception(
                f"Failed to download image. Returned status code: {upload_image_response.status_code}")
        
        return redirect("/gallery")
    
    return HttpResponse("Error when uploading image.")

def convert_image(request, slug):
    user_token = request.COOKIES.get('jwt')
    
    job_request = PublicImageProcessingJobRequest(job_name="job", 
                                                  resize_image_to_width=request.POST["width"], 
                                                  resize_image_to_height=request.POST["height"], 
                                                  change_to_format=request.POST["imageFormat"])
    
    print(job_request.model_dump())

    convert_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}/jobs"
    convert_image_response = requests.post(convert_image_url, 
                                           json=job_request.model_dump(), 
                                           headers={"Authorization": user_token})

    if convert_image_response.status_code != 200:
        raise Exception(
            f"Failed to submit job. Returned status code: {convert_image_response.status_code}")
    
    return redirect(f"/gallery/image/view/{slug}")
