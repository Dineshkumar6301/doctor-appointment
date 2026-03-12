# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Clinic

@receiver(post_save, sender=User)
def create_clinic_for_admin(sender, instance, created, **kwargs):

    if created and instance.is_clinic:
        Clinic.objects.get_or_create(
            admin=instance,
            defaults={
                "name": f"{instance.first_name} {instance.last_name}"
            }
        )