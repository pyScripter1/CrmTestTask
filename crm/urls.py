from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, DeveloperViewSet, project_kanban, project_files, project_files_tree, upload_project_files, create_project_folder

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'developers', DeveloperViewSet, basename='developer')

urlpatterns = [
    # DRF entities
    path('', include(router.urls)),

    # Kanban API
    path('kanban/', include('crm.api_urls')),

    # HTML kanban page
    path(
        "projects/<int:project_id>/kanban/<uuid:token>/",
        project_kanban,
        name="project-kanban",
    ),
    path(
        "projects/<uuid:project_uuid>/files/",
        project_files,
        name="project-files",
    ),

    path(
        "projects/<uuid:project_uuid>/files/tree/",
        project_files_tree
    ),
    path(
        "projects/<uuid:project_uuid>/files/upload/",
        upload_project_files
    ),
    path(
        "projects/<uuid:project_uuid>/folders/create/",
        create_project_folder
    ),



]
