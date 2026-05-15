from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


def is_admin(user):
    return hasattr(user, 'role') and user.role == 'ADMIN'


def is_methodist(user):
    return hasattr(user, 'role') and user.role == 'METHODIST'


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and is_admin(request.user)
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and is_admin(request.user)


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'requester'):
            return obj.requester == request.user
        return False


class CanCreatePublication(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return is_methodist(request.user) or is_admin(request.user)


class CanUpdateOwnPublication(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        return obj.owner == request.user


class CanDeletePublication(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        return obj.owner == request.user and obj.status == 'active'


class CanManageDeleteRequests(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and is_admin(request.user)


class CanViewLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and is_admin(request.user)


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and is_admin(request.user)


class CanManageUsers(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and is_admin(request.user)
