from rest_framework import permissions

class IsPremiumUser(permissions.BasePermission):
    """
    Allows access only to premium users.
    """
    message = 'You must be a premium user to access this feature.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_premium_user()
