from django.db import models

# Create your models here.
class AIG(models.Model):
	users = models.FloatField()
	bandwidth = models.FloatField()
	eventmarking = models.FloatField()
	eventtimestamp = models.CharField(max_length=100)
