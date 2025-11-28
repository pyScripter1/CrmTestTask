from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PM = 'PM', 'Project Manager'
        DEV = 'DEV', 'Developer'

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.DEV)

    def is_admin_role(self):
        return self.role == self.Roles.ADMIN

    def is_pm(self):
        return self.role == self.Roles.PM

    def is_dev(self):
        return self.role == self.Roles.DEV
