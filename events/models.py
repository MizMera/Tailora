from django.db import models

class Event(models.Model):
   

    name = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)
    capacity = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    dress_code = models.CharField(max_length=7)  # hex code, e.g., #430e0e


