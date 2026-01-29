"""
Role constants for MunTech School Infrastructure
"""

ROLES = {
    'STUDENT': 'student',
    'TEACHER': 'teacher',
    'GUARDIAN': 'guardian',
    'ADMIN': 'admin',
    'SCHOOL_ADMIN': 'school_admin',
    'STAFF': 'staff',
}

# Permissions by role
PERMISSIONS = {
    'student': ['view_own_attendance', 'view_own_grades', 'view_own_profile'],
    'teacher': ['view_class_attendance', 'mark_attendance', 'view_assigned_classes', 'view_all_students'],
    'school_admin': ['manage_staff', 'manage_classes', 'manage_students', 'view_reports'],
    'admin': ['manage_all', 'system_settings', 'manage_schools'],
}
