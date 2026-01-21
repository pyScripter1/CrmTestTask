from django.contrib import admin
from django import forms
from django.utils.html import format_html

from unfold.admin import ModelAdmin, TabularInline  # база из Unfold

from .models import Project, Developer


@admin.register(Project)
class ProjectAdmin(ModelAdmin):  # 👈 наследуемся от Unfold ModelAdmin
    list_display = (
        'name',
        'customer_name',
        'total_cost',
        'deadline',
        'completion_percent',
        'responsible',
    )
    list_filter = ('deadline', 'completion_percent', 'responsible')
    search_fields = ('name', 'customer_name')
    list_select_related = ('responsible',)

    # 👉 крассивый виджет выбора разработчиков (Unfold + autocomplete_fields)
    autocomplete_fields = ('developers',)

    readonly_fields = ("kanban_link", "files_link")

    change_form_template = "admin/crm/project/change_form.html"

    def get_fieldsets(self, request, obj=None):
        """
        Preserve the original field order (from get_fields), but move "attention_note"
        to a dedicated right sidebar fieldset.
        """
        # Базовый порядок полей — как раньше (учитывает роль в get_fields)
        fields = list(self.get_fields(request, obj))

        # Remove note from the main area; it will render in the sidebar
        if "attention_note" in fields:
            fields = [f for f in fields if f != "attention_note"]

        return (
            ("Project", {"fields": tuple(fields)}),
            ("⚠️ Обратите внимание", {"fields": ("attention_note",), "classes": ("please-note-fieldset",)}),
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "attention_note":
            kwargs["label"] = ""  # заголовок уже есть у правого блока
            kwargs["widget"] = forms.Textarea(attrs={"rows": 18, "style": "width:100%; min-height: 320px;"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        """
        PM creating a new project: default 'responsible' to themselves.
        """
        initial = super().get_changeform_initial_data(request)
        user = request.user

        # only on "add" page (no object yet), don't override explicit querystring initial
        if getattr(user, "is_pm", lambda: False)() and "responsible" not in initial:
            initial["responsible"] = user.pk

        return initial

    list_display_links = list_display


    @admin.display(description="Ответственный")
    def responsible_plain(self, obj):
        return str(obj.responsible) if obj and obj.responsible else "—"

    # === Права доступа к модулю и объектам ===

    def get_list_display(self, request):
        """
        Динамический список колонок в зависимости от роли пользователя.
        Разработчик НЕ видит customer_name и total_cost.
        """
        user = request.user

        # Админ и PM видят все поля
        if user.is_superuser or user.is_admin_role() or user.is_pm():
            return (
                'name',
                'customer_name',
                'total_cost',
                'deadline',
                'completion_percent',
                'responsible',
            )

        # Разработчик — только безопасные поля
        if user.is_dev():
            return ('name', 'deadline', 'completion_percent', 'responsible')

        # Остальные — ничего
        return ()

    def kanban_link(self, obj):
        # Проект ещё не сохранён (нет id)
        if not obj or not obj.pk:
            return format_html(
                '<span style="color: #999;">'
                'Сохраните проект, чтобы открыть канбан'
                '</span>'
            )

        url = f"/projects/{obj.id}/kanban/{obj.kanban_token}/"
        return format_html(
            """
            <a href="{url}" target="_blank" style="
                display: block;
                padding: 14px 16px;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                background:#0f172a;
                text-decoration: none;
                color: inherit;
                transition: background 0.15s ease;
            ">
                <div style="font-size: 14px;">
                    Открыть Канбан
                </div>
            </a>
            """,
            url=url
        )

    kanban_link.short_description = "Канбан"

    def files_link(self, obj):
        if not obj or not obj.pk:
            return "Сохраните проект"

        return format_html(
            """
            <a href="/projects/{uuid}/files/" target="_blank" style="
                display:block;
                padding:14px 16px;
                border:1px solid #d1d5db;
                border-radius:12px;
                background:#0f172a;
                text-decoration:none;
                color:inherit;
            ">
                <div style="font-weight:600;">Файлы проекта</div>
                <div style="font-size:12px;color:#6b7280;">
                    Папки и документы проекта
                </div>
            </a>
            """,
            uuid=obj.files_token,
        )

    files_link.short_description = "Файлы"

    def has_module_permission(self, request):
        """
        Модуль "Проекты" виден:
        - Админу (роль ADMIN или суперюзер)
        - Проект-менеджеру
        - Разработчику (read-only)
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if getattr(user, "is_admin_role", lambda: False)():
            return True
        if getattr(user, "is_pm", lambda: False)():
            return True
        if getattr(user, "is_dev", lambda: False)():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """
        Просматривать проекты могут:
        - Admin
        - PM
        - DEV
        Фактический список ограничивается get_queryset.
        """
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        """
        Создавать проекты могут:
        - Admin
        - PM
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if getattr(user, "is_admin_role", lambda: False)():
            return True
        if getattr(user, "is_pm", lambda: False)():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Менять проекты могут:
        - Admin (всегда)
        - PM, но только свои (где он responsible)
        Разработчики — могут менять только поле "⚠️ Обратите внимание" в своих проектах.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        if getattr(user, "is_pm", lambda: False)():
            # Если объекта нет (список) — разрешаем, дальше отфильтрует get_queryset
            if obj is None:
                return True
            return obj.responsible == user
        if getattr(user, "is_dev", lambda: False)():
            # Список/массовые операции не нужны — только change form конкретного проекта
            if obj is None:
                return False
            try:
                developer = user.developer_profile
                return obj.developers.filter(id=developer.id).exists()
            except Exception:
                return False
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Удалять проекты может только Admin.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        return False

    # === Фильтрация списка в зависимости от роли ===

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or user.is_admin_role():
            return qs
        if user.is_pm():
            return qs.filter(responsible=user)
        if user.is_dev():
            try:
                developer = user.developer_profile
                return qs.filter(developers=developer)
            except Exception:
                return qs.none()
        return qs.none()

    def get_fields(self, request, obj=None):
        """
        Явно контролируем порядок полей для DEV,
        чтобы он был таким же, как до правок.
        """
        user = request.user

        # --- DEV: фиксированный, правильный порядок ---
        if user.is_dev():
            fields = [
                "name",  # Название проекта
                "deadline",  # Дедлайн
                "completion_percent",  # Готовность
                "responsible",  # Ответственный
                "developers",  # Разработчики
                "stages",  # Этапы проекта
                "active_stage",  # Текущий этап
                "comments",  # Комментарии
            ]

            # Канбан показываем только для сохранённого проекта
            if obj:
                fields.append("kanban_link")

            return fields

        # --- НЕ DEV: стандартная логика ---
        fields = list(super().get_fields(request, obj))

        if obj and "kanban_link" not in fields:
            fields.insert(1, "kanban_link")

        return fields

    def get_readonly_fields(self, request, obj=None):
        """
        DEV может редактировать только attention_note; остальные поля read-only.
        """
        user = request.user
        if user and getattr(user, "is_dev", lambda: False)():
            # все реальные поля модели + объявленные readonly,
            # кроме attention_note (её оставляем редактируемой)
            model_fields = [f.name for f in self.model._meta.fields]
            m2m_fields = [m.name for m in self.model._meta.many_to_many]
            base = set(model_fields + m2m_fields)
            base.update(self.readonly_fields or ())
            if "attention_note" in base:
                base.remove("attention_note")
            return tuple(sorted(base))
        return super().get_readonly_fields(request, obj)



    def get_inline_instances(self, request, obj=None):
        """
        Разработчики не видят блок с документами вообще.
        Админ и PM видят и могут работать с файлами своих проектов.
        """
        user = request.user
        if getattr(user, "is_dev", lambda: False)():
            return []
        return super().get_inline_instances(request, obj)


@admin.register(Developer)
class DeveloperAdmin(ModelAdmin):  # 👈 тоже на базе Unfold
    list_display = ('full_name', 'position', 'cooperation_format', 'salary')
    list_filter = ('cooperation_format', 'position')
    search_fields = ('full_name', 'position', 'competencies')
    readonly_fields = ("user_plain",)

    @admin.display(description="Пользователь")
    def user_plain(self, obj):
        return str(obj.user) if obj and obj.user else "—"


    # === Права доступа к модулю и объектам ===

    def has_module_permission(self, request):
        """
        Модуль "Разработчики" виден:
        - Admin
        - PM
        - DEV (только свой профиль)
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if getattr(user, "is_admin_role", lambda: False)():
            return True
        if getattr(user, "is_pm", lambda: False)():
            return True
        if getattr(user, "is_dev", lambda: False)():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """
        Просмотр профилей разработчиков:
        - Admin: всех
        - PM: всех (чувствительные поля скрывает get_fields)
        - DEV: только свой объект
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        if getattr(user, "is_pm", lambda: False)():
            return True
        if getattr(user, "is_dev", lambda: False)():
            if obj is None:
                # Для списка — доступ есть, но get_queryset вернёт только своего
                return True
            return obj.user == user
        return False

    def has_add_permission(self, request):
        """
        Создавать разработчиков может только Admin.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Менять разработчиков:
        - Admin: любых
        - Остальные: нет (PM/DEV read-only через админку)
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Удалять разработчиков может только Admin.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "is_admin_role", lambda: False)():
            return True
        return False

    # === Ограничение списка и полей ===

    def get_readonly_fields(self, request, obj=None):
        # user всегда readonly после создания
        if obj:
            return ('user',)
        return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or user.is_admin_role():
            return qs
        if user.is_pm():
            # PM видит всех разработчиков
            return qs
        if user.is_dev():
            try:
                return qs.filter(user=user)
            except Exception:
                return qs.none()
        return qs.none()

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))

        # PM/DEV: заменяем поле user (FK-ссылка) на user_plain (обычный текст)
        if obj and (request.user.is_pm() or request.user.is_dev()):
            fields = ["user_plain" if f == "user" else f for f in fields]

        # PM не видит паспортные и контакты
        if request.user.is_pm():
            forbidden = ("passport_data", "contacts")
            fields = [f for f in fields if f not in forbidden]

        # DEV не видит паспорт, з/п, контакты
        if request.user.is_dev():
            forbidden = ("passport_data", "salary", "contacts")
            fields = [f for f in fields if f not in forbidden]

        return fields

