from django.urls import path
from .views import (
    kanban_state,
    kanban_task_create,
    kanban_task_update,
    kanban_task_delete,
    kanban_reorder,
    kanban_task_history,
    kanban_project_activity,
)

urlpatterns = [
    path("kanban/<int:project_id>/", kanban_state),
    path("kanban/task/", kanban_task_create),
    path("kanban/task/<int:task_id>/", kanban_task_update),
    path("kanban/task/<int:task_id>/delete/", kanban_task_delete),
    path("kanban/reorder/", kanban_reorder),
    path("kanban/task/<int:task_id>/history/", kanban_task_history),
    path("kanban/project/<int:project_id>/activity/", kanban_project_activity),

]
