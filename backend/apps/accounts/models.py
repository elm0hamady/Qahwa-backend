from django.contrib.auth.models import AbstractUser
from django.db import models



class Host(AbstractUser):
    email = models.EmailField(unique=True)