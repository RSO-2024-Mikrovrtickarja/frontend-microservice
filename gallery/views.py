from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import pybreaker

import frontend.settings
from .models import PublicImage, InternalImage, PublicImageProcessingJobRequest, ImageShareUrlInfo
from frontend.config import config
import os
from PIL import Image
from tempfile import SpooledTemporaryFile, NamedTemporaryFile
import base64
import io
from retry import retry

# Create your views here.

PHOTO_STORAGE_HOST = config.photo_storage_host
PHOTO_STORAGE_PORT = config.photo_storage_port

upscale_api_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=60)
photo_storage_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

def index(request):
    return HttpResponse("Hello, world.")

def download_image_request(image_id: str, user_token: str) -> requests.Response:
    download_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{image_id}/download"
    download_image_response = requests.get(download_image_url, headers={"Authorization": user_token})

    if download_image_response.status_code != 200:
        raise Exception(f"Failed to download image {image_id}. Returned status code: {download_image_response.status_code}")
    return download_image_response

def gallery(request, error_msg: str = ""):
    
    user_token = request.COOKIES.get('jwt')
    
    if not user_token:
         return redirect("/users/login")

    all_images_internal = {"images": []}
    get_all_images_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images"
    
    with photo_storage_breaker.calling():
        try:
            get_all_images_response = requests.get(get_all_images_url, headers={"Authorization": user_token})

            if get_all_images_response.status_code != 200:
                raise Exception(f"Failed to get all images. Returned status code: {get_all_images_response.status_code}")
        
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
        except pybreaker.CircuitBreakerError:
            error_msg = "Failed to retrieve images. Try again later."
        
    context = all_images_internal
    context["error_msg"] = error_msg
    
    return render(request, "gallery.html", context)

def view_image(request, slug):
    user_token = request.COOKIES.get('jwt')
    image_internal = {"image": []}
    get_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}"
    
    with photo_storage_breaker.calling():
        try:
            get_image_response = requests.get(get_image_url, headers={"Authorization": user_token})
        
            if get_image_response.status_code != 200:
                raise Exception(f"Failed to get image {slug}. Returned status code: {get_image_response.status_code}")
            
            image_public = get_image_response.json()
            
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
        except pybreaker.CircuitBreakerError:
            return gallery(request, error_msg="Failed to view image. Try again later.")
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

    share_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}/share-url"
    share_image_response = requests.post(share_image_url, headers={"Authorization": user_token})

    if share_image_response.status_code != 200:
        raise Exception(
            f"Failed to generate image share url {slug}. Returned status code: {share_image_response.status_code}")
    
    generated_url = ImageShareUrlInfo.model_validate(share_image_response.json())
    context = generated_url.model_dump()
    
    return render(request, "share.html", context)

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
                f"Failed to upload image. Returned status code: {upload_image_response.status_code}")
        
    return redirect("/gallery")

def convert_image(request, slug):
    user_token = request.COOKIES.get('jwt')
    
    job_request = PublicImageProcessingJobRequest(job_name="job", 
                                                  resize_image_to_width=request.POST["width"], 
                                                  resize_image_to_height=request.POST["height"], 
                                                  change_to_format=request.POST["imageFormat"])
    
    convert_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images/{slug}/jobs"
    convert_image_response = requests.post(convert_image_url, 
                                           json=job_request.model_dump(), 
                                           headers={"Authorization": user_token})

    if convert_image_response.status_code != 200:
        raise Exception(f"Failed to submit job. Returned status code: {convert_image_response.status_code}")
    
    return redirect(f"/gallery/image/view/{slug}")

@retry(exceptions=Exception, tries=2, delay=2)
@upscale_api_breaker
def call_external_upscale_api(url, headers, data, files):
    response = requests.post(url, headers=headers, data=data, files=files)
    print(response.json()["data"]["url"])
    
    if response.status_code != 200:
        raise Exception(f"Failed to upscale image. Returned status code: {response.status_code}. "
                        f"Err: {response.text}")
    return response

def upscale_image(request, slug):
    # Only JPG, PNG, TIFF and WEBP input image formats are supported!
    user_token = request.COOKIES.get('jwt')
    image_data_response = download_image_request(slug, user_token)

    intermediate_image_buffer = SpooledTemporaryFile(mode="w+b")
    intermediate_image_buffer.write(image_data_response.content)
    intermediate_image_buffer.seek(0, os.SEEK_SET)

    upscale_url = "https://api.picsart.io/tools/1.0/upscale"
    upscale_factor = request.POST["upscaleFactor"]
    api_key = config.upscale_api_key
    output_image_format = "JPG"

    data = {
        "upscale_factor": upscale_factor,  # Text field
        "format": output_image_format,  # Text field
    }

    files = {
        "image": intermediate_image_buffer
    }

    headers = {
        "accept": "application/json",
        "X-Picsart-API-Key": api_key,
    }
    
    upscale_response = None
    try:
        upscale_response = call_external_upscale_api(upscale_url, headers, data, files)
    except pybreaker.CircuitBreakerError:
        return gallery(request, error_msg="Upscaling functionality currently not available. Try again later.")


    filename = (
        image_data_response.headers.get("Content-Disposition", "")
        .split("filename=")[1]
        .strip('"')
    )
    filename = "upscaled_" + filename

    upscaled_image = Image.open(requests.get(upscale_response.json()["data"]["url"], stream=True).raw)
    upscaled_img_byte_arr = io.BytesIO()
    upscaled_image.save(upscaled_img_byte_arr, format='JPEG')
    upscaled_img_byte_arr = upscaled_img_byte_arr.getvalue()

    image = {"uploaded_file": (filename, upscaled_img_byte_arr)}

    upload_image_url = f"http://{PHOTO_STORAGE_HOST}:{PHOTO_STORAGE_PORT}/images"
    upload_image_response = requests.post(upload_image_url, files=image, headers={"Authorization": user_token})

    if upload_image_response.status_code != 200:
        raise Exception(
            f"Failed to upload image. Returned status code: {upload_image_response.status_code}")

    return redirect(f"/gallery")
