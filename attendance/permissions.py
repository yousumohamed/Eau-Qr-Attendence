from rest_framework import permissions


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow teachers and admins to create/manage sessions.
    """
    
    def has_permission(self, request, view):
        # Allow read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for staff/admin or users with teacher profile
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user has a teacher profile
        return hasattr(request.user, 'teacher_profile')
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Admin can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Teachers can only modify their own sessions
        if hasattr(request.user, 'teacher_profile'):
            return obj.teacher == request.user.teacher_profile
        
        return False


class IsAuthenticatedOrPublicScan(permissions.BasePermission):
    """
    Allow public access to scan endpoint, but require authentication for other operations.
    """
    
    def has_permission(self, request, view):
        # Allow scan endpoint to be public
        if view.action == 'scan':
            return True
        return request.user.is_authenticated
