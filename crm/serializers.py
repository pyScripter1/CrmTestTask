from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, Developer, KanbanTask, KanbanColumn, ProjectFolder, ProjectFile
from .models import KanbanTaskHistory

import logging


User = get_user_model()
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']




# ========== Developer Serializers (без изменений) ==========

class DeveloperBaseSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Developer
        fields = [
            'id', 'user', 'user_details', 'full_name', 'position',
            'cooperation_format', 'workload', 'competencies',
            'strengths', 'weaknesses', 'comments'
        ]
        read_only_fields = ['id', 'user', 'user_details']


class DeveloperAdminSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Developer
        fields = '__all__'
        read_only_fields = ['id', 'user']

    def get_projects_count(self, obj):
        return obj.projects.count()


class DeveloperPMSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Developer
        exclude = ['passport_data', 'contacts']
        read_only_fields = ['id', 'user', 'salary']

    def get_projects_count(self, obj):
        return obj.projects.count()


class DeveloperDeveloperSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Developer
        fields = [
            'id', 'user_details', 'full_name', 'position',
            'cooperation_format', 'workload', 'competencies',
            'strengths', 'weaknesses', 'comments'
        ]
        read_only_fields = fields


# ========== Project Serializers ==========

class ProjectBaseSerializer(serializers.ModelSerializer):
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'deadline', 'completion_percent',
            'responsible', 'responsible_details', 'developers',
            'developers_count', 'stages', 'active_stage', 'comments',
            'created_at', 'updated_at', 'documents'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_developers_count(self, obj):
        return obj.developers.count()


class ProjectAdminSerializer(ProjectBaseSerializer):
    developers_details = DeveloperBaseSerializer(source='developers', many=True, read_only=True)

    class Meta(ProjectBaseSerializer.Meta):
        fields = '__all__'


class ProjectPMSerializer(ProjectBaseSerializer):
    developers_details = DeveloperPMSerializer(source='developers', many=True, read_only=True)

    class Meta(ProjectBaseSerializer.Meta):
        fields = '__all__'


class ProjectDeveloperSerializer(serializers.ModelSerializer):
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ['customer_name', 'total_cost']
        read_only_fields = exclude

    def get_developers_count(self, obj):
        return obj.developers.count()


# ========== Lightweight List Serializers ==========

class DeveloperListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Developer
        fields = ['id', 'full_name', 'position', 'cooperation_format']


class ProjectListSerializer(serializers.ModelSerializer):
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'deadline', 'completion_percent',
            'responsible', 'responsible_name', 'developers_count',
            'active_stage', 'created_at'
        ]
        read_only_fields = fields

    def get_developers_count(self, obj):
        return obj.developers.count()


class KanbanColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanColumn
        fields = ("id", "code", "title", "order")



class KanbanTaskSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="column.code", read_only=True)

    # ВХОД: строка-токен ("customer", "user:1", "dev:2", "")
    assignee = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    # ВЫХОД: чтобы JS мог выставить select при edit
    assignee_value = serializers.SerializerMethodField(read_only=True)

    # ВЫХОД: чтобы показать на карточке
    assignee_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = KanbanTask
        fields = (
            "id",
            "project",
            "title",
            "description",
            "order",
            "status",
            "column",
            "deadline",
            "assignee",          # write-only token
            "assignee_value",    # read-only token
            "assignee_display",  # read-only text
            "updated_at",
        )

    def get_assignee_display(self, obj: KanbanTask) -> str:
        return obj.get_assignee_display()

    def get_assignee_value(self, obj: KanbanTask) -> str:
        if obj.assignee_kind == getattr(KanbanTask, "AssigneeKind").CUSTOMER:
            return "customer"
        if obj.assignee_kind == getattr(KanbanTask, "AssigneeKind").USER and obj.assignee_user_id:
            return f"user:{obj.assignee_user_id}"
        if obj.assignee_kind == getattr(KanbanTask, "AssigneeKind").DEVELOPER and obj.assignee_developer_id:
            return f"dev:{obj.assignee_developer_id}"
        return ""

    def _apply_assignee_token(self, task: KanbanTask, token: str):
        """
        Применяем token к задаче + валидируем, что исполнитель связан с проектом.
        """
        token = (token or "").strip()

        # сброс
        task.assignee_kind = KanbanTask.AssigneeKind.NONE
        task.assignee_user = None
        task.assignee_developer = None

        if token == "" or token == "none":
            return

        if token == "customer":
            task.assignee_kind = KanbanTask.AssigneeKind.CUSTOMER
            return

        # user:<id>
        if token.startswith("user:"):
            user_id = int(token.split(":", 1)[1])
            if task.project.responsible_id != user_id:
                raise serializers.ValidationError({"assignee": "Нельзя назначить этого пользователя: он не связан с проектом."})
            task.assignee_kind = KanbanTask.AssigneeKind.USER
            task.assignee_user_id = user_id
            return

        # dev:<id>
        if token.startswith("dev:"):
            dev_id = int(token.split(":", 1)[1])
            if not task.project.developers.filter(id=dev_id).exists():
                raise serializers.ValidationError({"assignee": "Нельзя назначить этого разработчика: он не связан с проектом."})
            task.assignee_kind = KanbanTask.AssigneeKind.DEVELOPER
            task.assignee_developer_id = dev_id
            return

        raise serializers.ValidationError({"assignee": "Некорректный формат исполнителя."})

    def update(self, instance, validated_data):
        # вытаскиваем токен исполнителя из initial_data (потому что поле write_only)
        token = None
        if "assignee" in self.initial_data:
            token = self.initial_data.get("assignee")

        instance = super().update(instance, validated_data)

        if token is not None:
            self._apply_assignee_token(instance, token)
            instance.save(update_fields=["assignee_kind", "assignee_user", "assignee_developer", "updated_at"])

        return instance

    def validate_deadline(self, value):
        """
        Разрешаем пустой дедлайн.
        """
        if value in ("", None):
            return None
        return value



class KanbanTaskHistorySerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()
    task = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)


    class Meta:
        model = KanbanTaskHistory
        fields = (
            "id",
            "project",
            "task",
            "action",
            "from_column",
            "to_column",
            "old_data",
            "new_data",
            "created_at",
            "user_display",
        )

    def get_user_display(self, obj):
        if not obj.user:
            return "System"
        # можно улучшить под твою модель User
        return getattr(obj.user, "email", None) or str(obj.user)

class ProjectFileSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = ProjectFile
        fields = (
            "id",
            "uuid",
            "filename",
            "url",
            "created_at",
        )

    def get_filename(self, obj):
        return obj.file.name.split("/")[-1]

class ProjectFolderTreeSerializer(serializers.ModelSerializer):
    folders = serializers.SerializerMethodField()
    files = ProjectFileSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectFolder
        fields = (
            "id",
            "uuid",
            "name",
            "folders",
            "files",
        )

    def get_folders(self, obj):
        children = obj.children.all().order_by("name")
        return ProjectFolderTreeSerializer(children, many=True).data


