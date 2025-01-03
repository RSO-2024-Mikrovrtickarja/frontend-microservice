from django.db import models
from django.template.defaultfilters import slugify
import uuid
from django.utils import timezone
from django.urls import reverse
from pydantic import BaseModel
from datetime import datetime

# Create your models here.

class PublicImage(BaseModel):
    id: uuid.UUID
    file_name: str
    uploaded_at: datetime


class InternalImage(BaseModel):
    id: str
    file_name: str
    file_format: str
    width: int
    height: int
    uploaded_at: str
    data: str

 
class PublicImageProcessingJobRequest(BaseModel):
    job_name: str

    resize_image_to_width: int
    resize_image_to_height: int
    change_to_format: str

class ImageShareUrlInfo(BaseModel):
    full_url: str

