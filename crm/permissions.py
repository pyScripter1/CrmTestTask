from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsAdminRole(permissions.BasePermission):
    """
    Permission check for Admin role (Gen Dir, Tech Dir).
    Admins can see and do everything.
    """
    def has_permission(self, request, view):
        try:
            return request.user and request.user.is_authenticated and (
                request.user.is_superuser or request.user.is_admin_role()
            )
        except Exception as e:
            logger.error(f"Error checking admin permission: {str(e)}")
            return False


class IsProjectManagerRole(permissions.BasePermission):
    """
    Permission check for Project Manager role.
    PMs can see their own projects and all developers.
    """
    def has_permission(self, request, view):
        try:
            return request.user and request.user.is_authenticated and (
                request.user.is_superuser or
                request.user.is_admin_role() or
                request.user.is_pm()
            )
        except Exception as e:
            logger.error(f"Error checking PM permission: {str(e)}")
            return False


class IsDeveloperRole(permissions.BasePermission):
    """
    Permission check for Developer role.
    Developers can see only their assigned projects.
    """
    def has_permission(self, request, view):
        try:
            return request.user and request.user.is_authenticated
        except Exception as e:
            logger.error(f"Error checking developer permission: {str(e)}")
            return False


class IsProjectResponsibleOrAdmin(permissions.BasePermission):
    """
    Object-level permission for projects.
    - Admin can access any project
    - PM can access their own projects
    - Developer can access projects they're assigned to
    """
    def has_object_permission(self, request, view, obj):
        try:
            # Admin can access everything
            if request.user.is_superuser or request.user.is_admin_role():
                return True

            # PM can access their own projects
            if request.user.is_pm():
                return obj.responsible == request.user

            # Developer can access projects they're assigned to
            if request.user.is_dev():
                try:
                    developer = request.user.developer_profile
                    return developer in obj.developers.all()
                except Exception:
                    return False

            return False
        except Exception as e:
            logger.error(f"Error checking project object permission: {str(e)}")
            return False


class IsDeveloperOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission for developer profiles.
    - Admin can access any developer profile
    - PM can view all developers (but not sensitive data)
    - Developer can only access their own profile
    """
    def has_object_permission(self, request, view, obj):
        try:
            # Admin can access everything
            if request.user.is_superuser or request.user.is_admin_role():
                return True

            # PM can view developers (serializer handles field filtering)
            if request.user.is_pm():
                return request.method in permissions.SAFE_METHODS

            # Developer can access only their own profile
            if request.user.is_dev():
                return obj.user == request.user

            return False
        except Exception as e:
            logger.error(f"Error checking developer object permission: {str(e)}")
            return False
