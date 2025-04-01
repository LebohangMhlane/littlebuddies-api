from django.db import models

# Create your models here.



class AppManager(models.Model):

    maintenance_mode_on = models.BooleanField(default=False)
    
    def __str__(self):
        return "App Manager"