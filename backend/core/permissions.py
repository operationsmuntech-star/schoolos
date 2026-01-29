"""
Custom permission classes for MunTech School Infrastructure
Phase 0: Skeleton role-based permissions
"""
from rest_framework import permissions
from backend.people.roles import ROLES


class IsTeacher(permissions.BasePermission):
    """Allow access only to teacher users"""
    def has_permission(self, request, view):
        return hasattr(request.user, 'person') and request.user.person.role == ROLES['TEACHER']


class IsStudent(permissions.BasePermission):
    """Allow access only to student users"""
    def has_permission(self, request, view):
        return hasattr(request.user, 'person') and request.user.person.role == ROLES['STUDENT']


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users"""
    def has_permission(self, request, view):
        return hasattr(request.user, 'person') and request.user.person.role == ROLES['ADMIN']


class IsSchoolAdmin(permissions.BasePermission):
    """Allow access only to school admin users"""
    def has_permission(self, request, view):
        return hasattr(request.user, 'person') and request.user.person.role in [ROLES['ADMIN'], ROLES['SCHOOL_ADMIN']]
