from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator

import uuid

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

    stages = models.TextField(
        blank=True,
        default='',
        verbose_name="Этапы проекта",
        help_text="Введите этапы проекта по порядку"
    )
    active_stage = models.CharField(max_length=255, blank=True, default='', verbose_name="Текущий этап")
    comments = models.TextField(blank=True, default='', verbose_name="Комментарии")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    kanban_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Токен канбана",
    )

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

# новые модели, для изоляции каждой доски для своего проекта
class KanbanColumn(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="kanban_columns",
    )

    code = models.CharField(
        max_length=32,
        verbose_name="Код колонки",
    )

    title = models.CharField(
        max_length=100,
        verbose_name="Название колонки",
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("project", "code")
        ordering = ["order"]

    def __str__(self):
        return f"{self.project.name} — {self.title}"



class KanbanTask(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="kanban_tasks",
        verbose_name="Проект",
    )
    column = models.ForeignKey(
        KanbanColumn,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Колонка",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    assignee = models.ForeignKey(
        Developer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Исполнитель",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Задача канбана"
        verbose_name_plural = "Задачи канбана"

    def __str__(self):
        return self.title




class KanbanTaskHistory(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_MOVE = "move"
    ACTION_REORDER = "reorder"
    ACTION_DELETE = "delete"

    ACTION_CHOICES = (
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_MOVE, "Move"),
        (ACTION_REORDER, "Reorder"),
        (ACTION_DELETE, "Delete"),
    )

    project = models.ForeignKey(
        "crm.Project",
        on_delete=models.CASCADE,
        related_name="kanban_activity",
    )
    task = models.ForeignKey(
        "crm.KanbanTask",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history",
        verbose_name="Задача канбана",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kanban_actions",
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    # Для move/reorder удобно видеть из/в какую колонку
    from_column = models.CharField(max_length=50, null=True, blank=True)
    to_column = models.CharField(max_length=50, null=True, blank=True)

    # Для update — что поменяли
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["task", "-created_at"]),
        ]

    def __str__(self):
        task_part = f"task={self.task_id}" if self.task_id else "task=deleted"
        return f"{self.project_id}:{task_part} {self.action} {self.created_at}"

