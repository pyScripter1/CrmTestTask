from django.contrib import admin
from .models import Project, Developer


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_name', 'total_cost', 'deadline', 'completion_percent', 'responsible')
    list_filter = ('deadline', 'completion_percent', 'responsible')
    search_fields = ('name', 'customer_name')
    list_select_related = ('responsible',)
    filter_horizontal = ('developers',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Admin (Gen Dir, Tech Dir) sees everything
        if request.user.is_superuser or request.user.is_admin_role():
            return qs

        # PM sees only their projects
        if request.user.is_pm():
            return qs.filter(responsible=request.user)

        # Developer sees only projects they're assigned to
        if request.user.is_dev():
            try:
                developer = request.user.developer_profile
                return qs.filter(developers=developer)
            except Exception:
                return qs.none()

        return qs.none()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        # Developer doesn't see: customer_name, total_cost, documents
        if request.user.is_dev():
            forbidden = ('customer_name', 'total_cost', 'documents')
            return [f for f in fields if f not in forbidden]

        # PM sees everything except documents (handled by admin)
        # Admin sees everything
        return fields


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'cooperation_format', 'salary')
    list_filter = ('cooperation_format', 'position')
    search_fields = ('full_name', 'position', 'competencies')
    # readonly_fields = ('user',)

    def get_readonly_fields(self, request, obj=None):
        # При редактировании — поле user readonly
        if obj:
            return ('user',)
        return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Admin sees all developers
        if request.user.is_superuser or request.user.is_admin_role():
            return qs

        # PM sees all developers
        if request.user.is_pm():
            return qs

        # Developer sees only their own profile
        if request.user.is_dev():
            try:
                return qs.filter(user=request.user)
            except Exception:
                return qs.none()

        return qs.none()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        # PM doesn't see passport_data, salary, contacts
        if request.user.is_pm():
            forbidden = ('passport_data', 'contacts')
            return [f for f in fields if f not in forbidden]

        # Developer doesn't see sensitive fields
        if request.user.is_dev():
            forbidden = ('passport_data', 'salary', 'contacts')
            return [f for f in fields if f not in forbidden]

        # Admin sees everything
        return fields
