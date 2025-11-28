from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, Developer
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']


# ========== Developer Serializers ==========

class DeveloperBaseSerializer(serializers.ModelSerializer):
    """Base serializer for Developer with common fields"""
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
    """Full serializer for Admin - sees everything including sensitive data"""
    user_details = UserSerializer(source='user', read_only=True)
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Developer
        fields = '__all__'
        read_only_fields = ['id', 'user']

    def get_projects_count(self, obj):
        try:
            return obj.projects.count()
        except Exception as e:
            logger.error(f"Error getting projects count: {str(e)}")
            return 0


class DeveloperPMSerializer(serializers.ModelSerializer):
    """Serializer for PM - excludes passport_data, salary, contacts"""
    user_details = UserSerializer(source='user', read_only=True)
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Developer
        exclude = ['passport_data', 'contacts']
        read_only_fields = ['id', 'user', 'salary']

    def get_projects_count(self, obj):
        try:
            return obj.projects.count()
        except Exception as e:
            logger.error(f"Error getting projects count: {str(e)}")
            return 0


class DeveloperDeveloperSerializer(serializers.ModelSerializer):
    """Serializer for Developer - sees only their own basic info"""
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
    """Base serializer for Project with common fields"""
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'deadline', 'completion_percent',
            'responsible', 'responsible_details', 'developers',
            'developers_count', 'stages', 'active_stage', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_developers_count(self, obj):
        try:
            return obj.developers.count()
        except Exception as e:
            logger.error(f"Error getting developers count: {str(e)}")
            return 0


class ProjectAdminSerializer(serializers.ModelSerializer):
    """Full serializer for Admin - sees everything"""
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_details = DeveloperBaseSerializer(source='developers', many=True, read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_developers_count(self, obj):
        try:
            return obj.developers.count()
        except Exception as e:
            logger.error(f"Error getting developers count: {str(e)}")
            return 0


class ProjectPMSerializer(serializers.ModelSerializer):
    """Serializer for PM - sees all project info"""
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_details = DeveloperPMSerializer(source='developers', many=True, read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_developers_count(self, obj):
        try:
            return obj.developers.count()
        except Exception as e:
            logger.error(f"Error getting developers count: {str(e)}")
            return 0


class ProjectDeveloperSerializer(serializers.ModelSerializer):
    """Serializer for Developer - excludes customer_name, total_cost, documents"""
    responsible_details = UserSerializer(source='responsible', read_only=True)
    developers_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ['customer_name', 'total_cost', 'documents']
        read_only_fields = exclude

    def get_developers_count(self, obj):
        try:
            return obj.developers.count()
        except Exception as e:
            logger.error(f"Error getting developers count: {str(e)}")
            return 0


# ========== List Serializers (lighter for list views) ==========

class DeveloperListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for developer lists"""
    class Meta:
        model = Developer
        fields = ['id', 'full_name', 'position', 'cooperation_format']


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists"""
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
        try:
            return obj.developers.count()
        except Exception as e:
            logger.error(f"Error getting developers count: {str(e)}")
            return 0
