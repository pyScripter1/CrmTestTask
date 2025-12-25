from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.db import transaction


import logging

from .models import Project, Developer, KanbanColumn, KanbanTask, KanbanTaskHistory
from .serializers import (
    ProjectAdminSerializer, ProjectPMSerializer, ProjectDeveloperSerializer, ProjectListSerializer,
    DeveloperAdminSerializer, DeveloperPMSerializer, DeveloperDeveloperSerializer, DeveloperListSerializer,
    KanbanTaskSerializer, KanbanColumnSerializer, KanbanTaskHistorySerializer
)
from .permissions import (
    IsAdminRole, IsProjectManagerRole, IsDeveloperRole,
    IsProjectResponsibleOrAdmin, IsDeveloperOwnerOrAdmin
)

logger = logging.getLogger(__name__)


# === Kanban defaults ===
DEFAULT_KANBAN_COLUMNS = [
    ("queue", "Очередь"),
    ("inprogress", "В работе"),
    ("help", "Нужна помощь"),
    ("blocked", "Заблокировано"),
    ("done", "Готово"),
]

def log_task_history(*, project, task, user, action, from_column=None, to_column=None, old_data=None, new_data=None):
    KanbanTaskHistory.objects.create(
        project=project,
        task=task,
        user=user if user.is_authenticated else None,
        action=action,
        from_column=from_column,
        to_column=to_column,
        old_data=old_data,
        new_data=new_data,
    )


def ensure_kanban_columns(project):
    """
    Гарантирует, что у проекта есть все стандартные колонки канбана.
    Безопасно вызывать много раз.
    """
    existing_codes = set(
        KanbanColumn.objects.filter(project=project)
        .values_list("code", flat=True)
    )

    with transaction.atomic():
        for order, (code, title) in enumerate(DEFAULT_KANBAN_COLUMNS):
            if code not in existing_codes:
                KanbanColumn.objects.create(
                    project=project,
                    code=code,
                    title=title,
                    order=order,
                )



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

def project_kanban(request, project_id: int, token):
    project = get_object_or_404(Project, id=project_id)

    # 1. Проверка токена (секретная ссылка)
    if project.kanban_token != token:
        raise Http404()

    user = request.user
    if not user.is_authenticated:
        raise Http404()

    # 2. Проверка доступа
    if user.is_superuser or user.is_admin_role():
        pass
    elif user.is_pm():
        if project.responsible_id != user.id:
            raise Http404()
    elif user.is_dev():
        try:
            developer = user.developer_profile
            if not project.developers.filter(id=developer.id).exists():
                raise Http404()
        except Exception:
            raise Http404()
    else:
        raise Http404()

    return render(
        request,
        "crm/kanban.html",
        {"project": project},
    )


@api_view(["GET"])
def kanban_state(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # проверка доступа (ТОЧНО та же логика, что и раньше)
    user = request.user
    if not user.is_authenticated:
        return Response(status=403)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (
            user.is_dev()
            and project.developers.filter(id=user.developer_profile.id).exists()
        )
    ):
        return Response(status=403)

    ensure_kanban_columns(project)

    columns = KanbanColumn.objects.filter(project=project)
    tasks = KanbanTask.objects.filter(project=project)

    return Response({
        "columns": KanbanColumnSerializer(columns, many=True).data,
        "tasks": KanbanTaskSerializer(tasks, many=True).data,
    })

@api_view(["POST"])
def kanban_task_create(request):
    project_id = request.data.get("project")
    title = request.data.get("title")
    status_code = request.data.get("status")
    order = request.data.get("order", 0)
    description = request.data.get("description", "")

    if not project_id or not title or not status_code:
        return Response(
            {"detail": "project, title, status обязательны"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = get_object_or_404(Project, id=project_id)

    # проверка доступа (ТОЧНО как у проекта)
    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (
            user.is_dev()
            and project.developers.filter(id=user.developer_profile.id).exists()
        )
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)


    # гарантируем наличие колонок
    ensure_kanban_columns(project)

    try:
        column = KanbanColumn.objects.get(
            project=project,
            code=status_code
        )
    except KanbanColumn.DoesNotExist:
        return Response(
            {"detail": f"Unknown kanban status: {status_code}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    task = KanbanTask.objects.create(
        project=project,
        column=column,
        title=title,
        description=description,
        order=order,
    )

    log_task_history(
        project=project,
        task=task,
        user=request.user,
        action=KanbanTaskHistory.ACTION_CREATE,
        to_column=column.code,
        new_data={"title": task.title, "description": task.description},
    )

    return Response(
        KanbanTaskSerializer(task).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def kanban_reorder(request):
    project_id = request.data.get("project")
    updates = request.data.get("updates", [])

    project = get_object_or_404(Project, id=project_id)

    # ✅ гарантируем наличие колонок
    ensure_kanban_columns(project)

    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (
            user.is_dev()
            and project.developers.filter(
                id=user.developer_profile.id
            ).exists()
        )
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    for item in updates:
        task_id = item.get("id")
        status_code = item.get("status")
        order = item.get("order", 0)

        if not task_id or not status_code:
            continue

        try:
            task = KanbanTask.objects.get(id=task_id, project=project)
            column = KanbanColumn.objects.get(project=project, code=status_code)
        except (KanbanTask.DoesNotExist, KanbanColumn.DoesNotExist):
            continue

        # сохраняем старое состояние
        old_status = task.column.code if task.column_id else None
        old_order = task.order

        # сохраняем новое состояние
        task.column = column
        task.order = order
        task.save(update_fields=["column", "order"])

        new_status = column.code
        new_order = order

        # лог перемещения между колонками
        if old_status != new_status:
            log_task_history(
                project=project,
                task=task,
                user=user,
                action=KanbanTaskHistory.ACTION_MOVE,
                from_column=old_status,
                to_column=new_status,
                new_data={"title": task.title},
            )

        # лог изменения порядка
        elif old_order != new_order:
            log_task_history(
                project=project,
                task=task,
                user=user,
                action=KanbanTaskHistory.ACTION_REORDER,
                from_column=new_status,
                to_column=new_status,
                old_data={"order": old_order},
                new_data={"order": new_order},
            )

    return Response({"detail": "ok"})





@api_view(["PATCH"])
def kanban_task_update(request, task_id):
    task = get_object_or_404(KanbanTask, id=task_id)

    # доступ по проекту
    project = task.project
    user = request.user

    if not user.is_authenticated:
        return Response(status=403)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (
            user.is_dev()
            and project.developers.filter(id=user.developer_profile.id).exists()
        )
    ):
        return Response(status=403)

    # сохраняем старое состояние
    old_data = {
        "title": task.title,
        "description": task.description,
        "status": task.column.code if task.column_id else None,
    }

    serializer = KanbanTaskSerializer(task, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # собираем новое состояние
    new_data = {
        "title": task.title,
        "description": task.description,
        "status": task.column.code if task.column_id else None,
    }

    # логируем перемещение
    if old_data["status"] != new_data["status"]:
        log_task_history(
            project=project,
            task=task,
            user=user,
            action=KanbanTaskHistory.ACTION_MOVE,
            from_column=old_data["status"],
            to_column=new_data["status"],
            new_data={"title": task.title},
        )

    # логируем изменение текста
    changed_fields = {
        k for k in ("title", "description")
        if old_data.get(k) != new_data.get(k)
    }

    if changed_fields:
        log_task_history(
            project=project,
            task=task,
            user=user,
            action=KanbanTaskHistory.ACTION_UPDATE,
            old_data={k: old_data[k] for k in changed_fields},
            new_data={**{k: new_data[k] for k in changed_fields}, "title": task.title},
        )

    return Response(serializer.data)



@api_view(["DELETE"])
def kanban_task_delete(request, task_id):
    task = get_object_or_404(KanbanTask, id=task_id)
    project = task.project

    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    log_task_history(
        project=project,
        task=task,
        user=request.user,
        action=KanbanTaskHistory.ACTION_DELETE,
        from_column=task.column.code if task.column_id else None,
        old_data={"title": task.title},
    )

    task.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def kanban_task_history(request, task_id: int):
    task = get_object_or_404(KanbanTask, id=task_id)
    project = task.project

    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN)

    # те же правила доступа, что в kanban_state
    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (user.is_dev() and project.developers.filter(id=user.developer_profile.id).exists())
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    qs = KanbanTaskHistory.objects.filter(task=task).order_by("-created_at")[:200]
    return Response(KanbanTaskHistorySerializer(qs, many=True).data)


@api_view(["GET"])
def kanban_project_activity(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if not (
        user.is_superuser
        or user.is_admin_role()
        or (user.is_pm() and project.responsible_id == user.id)
        or (user.is_dev() and project.developers.filter(id=user.developer_profile.id).exists())
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    qs = KanbanTaskHistory.objects.filter(project=project).order_by("-created_at")[:300]
    return Response(KanbanTaskHistorySerializer(qs, many=True).data)
