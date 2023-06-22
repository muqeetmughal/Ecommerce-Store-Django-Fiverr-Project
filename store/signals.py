from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Customer

@receiver(post_save, sender=User, dispatch_uid='save_customer')
def save_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        customer = Customer(user=user)
        customer.save()

post_save.connect(save_profile, sender=User)