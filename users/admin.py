# CrmAiStrategy/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

# Убираем Tokens и Groups из админки
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group

# Аккуратно удаляем Token, если он зарегистрирован
try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass

# Аккуратно удаляем Group, если он зарегистрирован
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Кастомная админка для User:
    - Показываем только основные поля (username, full_name, email, role)
    - Не показываем группы и permissions (они есть, но скрыты от UI)
    - Доступ к разделу пользователей только у ADMIN-роли и суперпользователя
    """

    # Убираем стандартные fieldsets DjangoUserAdmin, оставляем только нужные поля
    fieldsets = (
        ("Основная информация", {
            "fields": ("username", "password", "full_name", "email", "role")
        }),
    )

    add_fieldsets = (
        ("Создание пользователя", {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "full_name", "email", "role"),
        }),
    )

    # Поля в списке
    list_display = ("username", "full_name", "email", "role")
    list_filter = ("role",)

    filter_horizontal = ()
    ordering = ("username",)

    # Исключаем только first_name/last_name, т.к. их нет в модели
    # Остальные служебные поля (is_staff, is_active, is_superuser, groups, user_permissions)
    # не попадают в форму, т.к. не входят в fieldsets, но остаются рабочими в модели.
    exclude = ("first_name", "last_name")

    def has_module_permission(self, request):
        """
        Доступ к разделу пользователей в админке:
        - суперюзер
        - ADMIN по роли (ген. дир, тех. дир)
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        # метод is_admin_role определён в модели User
        return getattr(user, "is_admin_role", lambda: False)()

    def has_view_permission(self, request, obj=None):
        # Просмотр пользователей — тем же, кому разрешён модуль
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        # Менять пользователей может только админ/суперпользователь
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
