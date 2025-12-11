from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator

User = settings.AUTH_USER_MODEL


class Developer(models.Model):
    class CooperationFormat(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Полная занятость'
        PART_TIME = 'PART_TIME', 'Частичная занятость'
        OUTSOURCE = 'OUTSOURCE', 'Аутсорс'
        CONTRACT = 'CONTRACT', 'Контракт'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='developer_profile',
        verbose_name="Пользователь"
    )

    full_name = models.CharField(max_length=255, db_index=True, default='', verbose_name="ФИО")
    position = models.CharField(max_length=255, blank=True, default='', verbose_name="Должность")
    cooperation_format = models.CharField(
        max_length=50, choices=CooperationFormat.choices,
        default=CooperationFormat.FULL_TIME, blank=True, verbose_name="Формат сотрудничества"
    )
    contacts = models.TextField(blank=True, default='', verbose_name="Контакты")
    passport_data = models.TextField(blank=True, null=True, verbose_name="Паспортные данные")
    salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)], blank=True, null=True, verbose_name="Зарплата"
    )
    workload = models.CharField(max_length=255, blank=True, default='', verbose_name="Занятость")
    competencies = models.TextField(blank=True, default='', verbose_name="Компетенции")
    strengths = models.TextField(blank=True, default='', verbose_name="Сильные стороны")
    weaknesses = models.TextField(blank=True, default='', verbose_name="Слабые стороны")
    comments = models.TextField(blank=True, default='', verbose_name="Комментарии")

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Разработчик'
        verbose_name_plural = 'Разработчики'

    def __str__(self):
        return self.full_name


class Project(models.Model):
    name = models.CharField(max_length=255, db_index=True, default='', verbose_name="Название проекта")
    customer_name = models.CharField(max_length=255, db_index=True, blank=True, default='', verbose_name="Заказчик")
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)],
        blank=True, null=True, verbose_name="Общая сумма"
    )
    deadline = models.DateField(blank=True, null=True, db_index=True, verbose_name="Дедлайн")
    completion_percent = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Готовность (%)"
    )
    responsible = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='responsible_projects', verbose_name="Ответственный"
    )


    developers = models.ManyToManyField(Developer, related_name='projects', blank=True, verbose_name="Разработчики")

    stages = models.JSONField(default=list, blank=True, verbose_name="Этапы проекта")
    active_stage = models.CharField(max_length=255, blank=True, default='', verbose_name="Текущий этап")
    comments = models.TextField(blank=True, default='', verbose_name="Комментарии")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.name


# Новая модель для множества файлов

class ProjectDocument(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='documents', verbose_name="Проект"
    )

    file = models.FileField(
        upload_to='project_documents/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'zip', 'rar']
        )],
        verbose_name="Файл",
        help_text="Допустимые форматы: pdf, doc, docx, txt, xls, xlsx, zip, rar"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Документ проекта"
        verbose_name_plural = "Документы проекта"

    def __str__(self):
        return f"{self.project.name} — {self.file.name}"
