from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, DeveloperViewSet, project_kanban

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
]
