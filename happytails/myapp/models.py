from django.db import models
from django.contrib.auth.models import User 

# Create your models here.

class Animal(models.Model):
    ANIMAL_SIZES = (
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    )
    
    ADOPTION_STATUSES = (
    ("AV", "Disponibil"),   
    ("PD", "În proces"),      
    ("AD", "Adoptat"), 
    )

    name = models.CharField(max_length=200)
    breed = models.CharField(max_length=300)
    age = models.CharField(max_length=100)
    size = models.CharField(max_length=1, choices=ANIMAL_SIZES)
    story = models.CharField(max_length=500)
    image = models.ImageField(upload_to='animals/', blank=True, null=True)
    status = models.CharField(
        max_length=2,
        choices=ADOPTION_STATUSES,
        default="AV"
    )

    favorites = models.ManyToManyField(User, related_name='favorite_animals', blank=True)