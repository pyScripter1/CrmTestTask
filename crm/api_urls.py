from django.urls import path
from .views import (
    upload_project_files,
    create_project_folder,
    project_files_tree,
    delete_project_file,
    delete_project_folder,
    move_project_file,
    kanban_assignees,
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
    path("kanban/<int:project_id>/assignees/", kanban_assignees),
    path("kanban/task/", kanban_task_create),
    path("kanban/task/<int:task_id>/", kanban_task_update),
    path("kanban/task/<int:task_id>/delete/", kanban_task_delete),
    path("kanban/reorder/", kanban_reorder),
    path("kanban/task/<int:task_id>/history/", kanban_task_history),
    path("kanban/project/<int:project_id>/activity/", kanban_project_activity),
    path(
        "projects/<uuid:project_uuid>/files/upload/",
        upload_project_files,
        name="api_project_files_upload",
    ),
    path(
        "projects/<uuid:project_uuid>/folders/create/",
        create_project_folder,
        name="api_project_folder_create",
    ),
    path(
        "projects/<uuid:project_uuid>/files/tree/",
        project_files_tree,
        name="api_project_files_tree",
    ),
    path(
        "projects/<uuid:project_uuid>/files/<uuid:file_uuid>/delete/",
        delete_project_file,
        name="api_project_file_delete",
    ),
    path(
        "projects/<uuid:project_uuid>/folders/<uuid:folder_uuid>/delete/",
        delete_project_folder,
        name="api_project_folder_delete",
    ),
    path(
        "projects/<uuid:project_uuid>/files/<uuid:file_uuid>/move/",
        move_project_file,
        name="api_project_file_move",
    ),



]
