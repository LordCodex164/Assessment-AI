# permissions.py
from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Permission check for staff users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'staff'
        )


class IsStudentUser(BasePermission):
    """
    Permission check for student users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'student'
        )


class IsStaffOrReadOnly(BasePermission):
    """
    Staff can do anything, students can only read
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'staff'
        )