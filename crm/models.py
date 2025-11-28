from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator


User = settings.AUTH_USER_MODEL


# ----------- Developer ------------------

class Developer(models.Model):
    class CooperationFormat(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full-time'
        PART_TIME = 'PART_TIME', 'Part-time'
        OUTSOURCE = 'OUTSOURCE', 'Outsource'
        CONTRACT = 'CONTRACT', 'Contract'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')

    full_name = models.CharField(max_length=255, db_index=True)
    position = models.CharField(max_length=255)
    cooperation_format = models.CharField(
        max_length=50,
        choices=CooperationFormat.choices,
        default=CooperationFormat.FULL_TIME
    )
    contacts = models.TextField(help_text="Телефоны, email")
    passport_data = models.TextField(
        blank=True,
        null=True,
        help_text="Паспортные данные (будут зашифрованы)"
    )
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    workload = models.CharField(max_length=255)
    competencies = models.TextField()
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Developer'
        verbose_name_plural = 'Developers'

    def __str__(self):
        return self.full_name


# ----------- Project ------------------

class Project(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    customer_name = models.CharField(max_length=255, db_index=True)
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    deadline = models.DateField(db_index=True)
    completion_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Процент завершения (0-100)"
    )

    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='responsible_projects',
        help_text="PM или Admin, ответственный за проект"
    )

    documents = models.FileField(
        upload_to='project_documents/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx']
            )
        ]
    )

    developers = models.ManyToManyField(
        Developer,
        related_name='projects',
        blank=True,
    )

    stages = models.JSONField(
        default=list,
        blank=True,
        help_text="Все этапы проекта в формате [{name: 'Этап 1', status: 'in_progress', deadline: '2024-01-01'}]"
    )
    active_stage = models.CharField(
        max_length=255,
        blank=True,
        help_text="Текущий этап"
    )

    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.name
