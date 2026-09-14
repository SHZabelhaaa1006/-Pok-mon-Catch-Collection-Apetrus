from rest_framework.permissions import BasePermission

class IsAdminProfile(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.profile.is_admin)
