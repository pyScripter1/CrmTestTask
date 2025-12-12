from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms

from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group

from unfold.admin import ModelAdmin
from .models import User


# Убираем Tokens и Groups из админки
try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class UnfoldUserCreationForm(UserCreationForm):
    """
    Форма создания пользователя.
    Делаем password1/password2 визуально заметными через attrs виджета (без отдельного CSS).
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "full_name", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # делаем поля пароля заметными: рамка/фон/отступы (через inline attrs)
        for name in ("password1", "password2"):
            if name in self.fields:
                self.fields[name].widget = forms.PasswordInput(render_value=False)
                self.fields[name].widget.attrs.update({
                    "autocomplete": "new-password",
                    "placeholder": "Введите пароль" if name == "password1" else "Повторите пароль",
                })


@admin.register(User)
class UserAdmin(ModelAdmin, DjangoUserAdmin):
    """
    Кастомная админка для User (как у тебя было), но на Unfold
    + исправлена видимость password-полей на add-form.
    """

    add_form = UnfoldUserCreationForm  # ✅ важно!

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

    list_display = ("username", "full_name", "email", "role")
    list_filter = ("role",)
    ordering = ("username",)

    exclude = ("first_name", "last_name")
    filter_horizontal = ()

    def has_module_permission(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "is_admin_role", lambda: False)()

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
