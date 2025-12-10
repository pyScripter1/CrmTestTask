# CrmAiStrategy/crm/admin.py

from django.contrib import admin
from .models import Project, Developer


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_name', 'total_cost', 'deadline', 'completion_percent', 'responsible')
    list_filter = ('deadline', 'completion_percent', 'responsible')
    search_fields = ('name', 'customer_name')
    list_select_related = ('responsible',)
    autocomplete_fields = ('developers',)

    def get_list_display(self, request):
        """
        Динамический список колонок в зависимости от роли пользователя.
        Разработчик НЕ видит customer_name и total_cost.
        """
        user = request.user

        # Админ и PM видят все поля
        if user.is_superuser or user.is_admin_role() or user.is_pm():
            return ('name', 'customer_name', 'total_cost', 'deadline', 'completion_percent', 'responsible')

        # Разработчик — только безопасные поля
        if user.is_dev():
            return ('name', 'deadline', 'completion_percent', 'responsible')

        # Остальные — ничего
        return ()

    # === Права доступа к модулю и объектам ===

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
        Разработчики — только просмотр.
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
        # Разработчики не меняют проекты
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
        fields = super().get_fields(request, obj)
        # Разраб не видит финансы и документы
        if request.user.is_dev():
            forbidden = ('customer_name', 'total_cost', 'documents')
            return [f for f in fields if f not in forbidden]
        return fields


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'cooperation_format', 'salary')
    list_filter = ('cooperation_format', 'position')
    search_fields = ('full_name', 'position', 'competencies')

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
        fields = super().get_fields(request, obj)
        # PM не видит паспортные и контакты
        if request.user.is_pm():
            forbidden = ('passport_data', 'contacts')
            return [f for f in fields if f not in forbidden]
        # DEV не видит паспорт, з/п, контакты
        if request.user.is_dev():
            forbidden = ('passport_data', 'salary', 'contacts')
            return [f for f in fields if f not in forbidden]
        return fields
