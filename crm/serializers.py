from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, Developer, ProjectDocument, KanbanTask, KanbanColumn
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']


# === Документы (read-only) ===
class ProjectDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


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
    documents = ProjectDocumentSerializer(many=True, read_only=True)

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
    documents = ProjectDocumentSerializer(many=True, read_only=True)

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
    status = serializers.CharField(
        source="column.code",
        read_only=True
    )

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
            "assignee",
            "updated_at",
        )

