from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from .models import Project, Developer
from .serializers import (
    ProjectAdminSerializer, ProjectPMSerializer, ProjectDeveloperSerializer, ProjectListSerializer,
    DeveloperAdminSerializer, DeveloperPMSerializer, DeveloperDeveloperSerializer, DeveloperListSerializer
)
from .permissions import (
    IsAdminRole, IsProjectManagerRole, IsDeveloperRole,
    IsProjectResponsibleOrAdmin, IsDeveloperOwnerOrAdmin
)

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project model with role-based permissions and serializers.

    - Admin: Full access to all projects
    - PM: Access to their own projects
    - Developer: Read-only access to assigned projects
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['completion_percent', 'responsible', 'deadline']
    search_fields = ['name', 'customer_name', 'active_stage']
    ordering_fields = ['deadline', 'completion_percent', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user role"""
        try:
            user = self.request.user

            # Admin sees all projects
            if user.is_superuser or user.is_admin_role():
                return Project.objects.select_related('responsible').prefetch_related('developers').all()

            # PM sees only their projects
            if user.is_pm():
                return Project.objects.filter(
                    responsible=user
                ).select_related('responsible').prefetch_related('developers')

            # Developer sees only assigned projects
            if user.is_dev():
                try:
                    developer = user.developer_profile
                    return Project.objects.filter(
                        developers=developer
                    ).select_related('responsible').prefetch_related('developers')
                except Exception as e:
                    logger.error(f"Error getting developer profile: {str(e)}")
                    return Project.objects.none()

            return Project.objects.none()

        except Exception as e:
            logger.error(f"Error in ProjectViewSet.get_queryset: {str(e)}")
            return Project.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on user role and action"""
        try:
            user = self.request.user

            # Use lightweight serializer for list view
            if self.action == 'list':
                return ProjectListSerializer

            # Admin gets full serializer
            if user.is_superuser or user.is_admin_role():
                return ProjectAdminSerializer

            # PM gets PM serializer
            if user.is_pm():
                return ProjectPMSerializer

            # Developer gets limited serializer
            if user.is_dev():
                return ProjectDeveloperSerializer

            return ProjectListSerializer

        except Exception as e:
            logger.error(f"Error in ProjectViewSet.get_serializer_class: {str(e)}")
            return ProjectListSerializer

    def get_permissions(self):
        """Different permissions for different actions"""
        try:
            if self.action in ['create', 'update', 'partial_update', 'destroy']:
                # Only Admin and PM can modify
                return [IsAuthenticated(), IsProjectManagerRole()]
            return [IsAuthenticated(), IsProjectResponsibleOrAdmin()]
        except Exception as e:
            logger.error(f"Error in ProjectViewSet.get_permissions: {str(e)}")
            return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create project with error handling"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return Response(
                {"error": "Failed to create project", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Update project with error handling"""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            return Response(
                {"error": "Failed to update project", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """Delete project with error handling"""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            return Response(
                {"error": "Failed to delete project", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def developers(self, request, pk=None):
        """Get all developers assigned to this project"""
        try:
            project = self.get_object()
            developers = project.developers.all()
            serializer = DeveloperListSerializer(developers, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting project developers: {str(e)}")
            return Response(
                {"error": "Failed to get developers", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DeveloperViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Developer model with role-based permissions and serializers.

    - Admin: Full access to all developers
    - PM: View access to all developers (excluding sensitive data)
    - Developer: Access only to their own profile
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cooperation_format', 'position']
    search_fields = ['full_name', 'position', 'competencies']
    ordering_fields = ['full_name', 'position', 'salary']
    ordering = ['full_name']

    def get_queryset(self):
        """Filter queryset based on user role"""
        try:
            user = self.request.user

            # Admin sees all developers
            if user.is_superuser or user.is_admin_role():
                return Developer.objects.select_related('user').prefetch_related('projects').all()

            # PM sees all developers
            if user.is_pm():
                return Developer.objects.select_related('user').prefetch_related('projects').all()

            # Developer sees only their own profile
            if user.is_dev():
                try:
                    return Developer.objects.filter(user=user).select_related('user')
                except Exception as e:
                    logger.error(f"Error getting developer profile: {str(e)}")
                    return Developer.objects.none()

            return Developer.objects.none()

        except Exception as e:
            logger.error(f"Error in DeveloperViewSet.get_queryset: {str(e)}")
            return Developer.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on user role and action"""
        try:
            user = self.request.user

            # Use lightweight serializer for list view (non-admins)
            if self.action == 'list' and not (user.is_superuser or user.is_admin_role()):
                return DeveloperListSerializer

            # Admin gets full serializer
            if user.is_superuser or user.is_admin_role():
                return DeveloperAdminSerializer

            # PM gets PM serializer (no sensitive data)
            if user.is_pm():
                return DeveloperPMSerializer

            # Developer gets limited serializer
            if user.is_dev():
                return DeveloperDeveloperSerializer

            return DeveloperListSerializer

        except Exception as e:
            logger.error(f"Error in DeveloperViewSet.get_serializer_class: {str(e)}")
            return DeveloperListSerializer

    def get_permissions(self):
        """Different permissions for different actions"""
        try:
            if self.action in ['create', 'update', 'partial_update', 'destroy']:
                # Only Admin can create/modify/delete developers
                return [IsAuthenticated(), IsAdminRole()]
            return [IsAuthenticated(), IsDeveloperOwnerOrAdmin()]
        except Exception as e:
            logger.error(f"Error in DeveloperViewSet.get_permissions: {str(e)}")
            return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create developer with error handling"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating developer: {str(e)}")
            return Response(
                {"error": "Failed to create developer", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Update developer with error handling"""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error updating developer: {str(e)}")
            return Response(
                {"error": "Failed to update developer", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """Delete developer with error handling"""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting developer: {str(e)}")
            return Response(
                {"error": "Failed to delete developer", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects for this developer"""
        try:
            developer = self.get_object()
            projects = developer.projects.all()
            serializer = ProjectListSerializer(projects, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting developer projects: {str(e)}")
            return Response(
                {"error": "Failed to get projects", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
