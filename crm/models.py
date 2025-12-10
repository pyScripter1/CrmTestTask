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

    full_name = models.CharField(
        max_length=255,
        db_index=True,
        blank=False,
        null=False,
        default='',
        verbose_name="ФИО"
    )

    position = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Должность"
    )

    cooperation_format = models.CharField(
        max_length=50,
        choices=CooperationFormat.choices,
        default=CooperationFormat.FULL_TIME,
        blank=True,
        verbose_name="Формат сотрудничества"
    )

    contacts = models.TextField(
        help_text="Телефоны, email и другие контакты",
        blank=True,
        default='',
        verbose_name="Контакты"
    )

    passport_data = models.TextField(
        blank=True,
        null=True,
        help_text="Паспортные данные (конфиденциально)",
        verbose_name="Паспортные данные"
    )

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        verbose_name="Зарплата",
        help_text="Зарплата в рублях"
    )

    workload = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Занятость",
        help_text="Например: 80%, занят до конца месяца"
    )

    competencies = models.TextField(
        blank=True,
        default='',
        verbose_name="Компетенции",
        help_text="Технологии, языки программирования, фреймворки"
    )

    strengths = models.TextField(
        blank=True,
        default='',
        verbose_name="Сильные стороны"
    )

    weaknesses = models.TextField(
        blank=True,
        default='',
        verbose_name="Слабые стороны"
    )

    comments = models.TextField(
        blank=True,
        default='',
        verbose_name="Комментарии"
    )

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Разработчик'
        verbose_name_plural = 'Разработчики'

    def __str__(self):
        return self.full_name


class Project(models.Model):
    name = models.CharField(
        max_length=255,
        db_index=True,
        blank=False,
        null=False,
        default='',
        verbose_name="Название проекта"
    )

    customer_name = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        default='',
        verbose_name="Наименование заказчика"
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        verbose_name="Общая сумма",
        help_text="Общая стоимость в рублях"
    )

    deadline = models.DateField(
        db_index=True,
        blank=True,
        null=True,
        verbose_name="Общий дедлайн"
    )

    completion_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Процент выполнения",
        blank=True,
        verbose_name="Готовность (%)"
    )

    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_projects',
        help_text="Ответственный менеджер проекта или администратор",
        verbose_name="Ответственный"
    )

    documents = models.FileField(
        upload_to='project_documents/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'zip', 'rar']
        )],
        verbose_name="Документы проекта",
        help_text="Договоры, NDA, Акты и др."
    )

    developers = models.ManyToManyField(
        Developer,
        related_name='projects',
        blank=True,
        verbose_name="Разработчики"
    )

    stages = models.JSONField(
        default=list,
        blank=True,
        help_text="Этапы проекта в формате JSON",
        verbose_name="Этапы проекта"
    )

    active_stage = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Текущий этап"
    )

    comments = models.TextField(
        blank=True,
        default='',
        verbose_name="Комментарии"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.name