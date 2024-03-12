from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

class UserAccount(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=False)
    phone_number = models.PositiveIntegerField(max_length=10, blank=False, null=True, unique=True)
    is_customer = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.username}'s - User Account"
    
@receiver(post_save, sender=User)
def create_user_account(sender, user_instance, **kwargs):
    user_account = UserAccount()
    user_account.user = user_instance
    user_account.save()

