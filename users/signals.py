from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from crm.models import Developer

@receiver(post_save, sender=User)
def create_or_update_developer_profile(sender, instance, created, **kwargs):
    """
    Создаем Developer для пользователя с ролью DEV.
    Синхронизируем full_name.
    """
    if instance.role == User.Roles.DEV:
        # Получаем или создаем Developer
        developer, _ = Developer.objects.get_or_create(
            user=instance,
            defaults={'full_name': instance.full_name}
        )
        # Обновляем full_name, если он изменился
        if developer.full_name != instance.full_name:
            developer.full_name = instance.full_name
            developer.save()
