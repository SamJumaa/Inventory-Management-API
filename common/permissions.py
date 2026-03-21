from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCompanyAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if not hasattr(user, "profile"):
            return False

        return user.profile.role in ["owner", "admin"]
