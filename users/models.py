from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PM = 'PM', 'Менеджер проекта'
        DEV = 'DEV', 'Разработчик'

    # Удаляем first_name, last_name, вводим обязательное поле full_name
    first_name = None
    last_name = None

    full_name = models.CharField(
        max_length=255,
        verbose_name="ФИО",
        null=False,
        blank=False,
        default="",
        help_text="Полное имя пользователя",
    )

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.ADMIN,
        verbose_name="Роль пользователя",
    )

    # Значения по умолчанию
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Админ всегда суперюзер
        if self.role == self.Roles.ADMIN:
            self.is_superuser = True
        super().save(*args, **kwargs)

    # Методы ролей
    def is_admin_role(self):
        return self.role == self.Roles.ADMIN

    def is_pm(self):
        return self.role == self.Roles.PM

    def is_dev(self):
        return self.role == self.Roles.DEV

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.full_name
