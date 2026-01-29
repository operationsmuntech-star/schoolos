"""
Core business logic services
Phase 0: Skeleton service layer
"""


class SchoolService:
    """School management services"""
    
    @staticmethod
    def get_active_term(school):
        """Get active academic term for school"""
        from backend.core.models import Term
        return Term.objects.filter(school=school, is_active=True).first()
    
    @staticmethod
    def get_school_classes(school):
        """Get all classes in school"""
        from backend.core.models import Class
        return Class.objects.filter(school=school)
    
    @staticmethod
    def get_class_students(klass):
        """Get all students in class"""
        from backend.people.models import Student
        return Student.objects.filter(current_class=klass)


class AttendanceService:
    """Attendance calculation and reporting services"""
    
    @staticmethod
    def calculate_attendance_rate(student, term=None):
        """Calculate student attendance rate for term"""
        pass
    
    @staticmethod
    def get_absentees(klass, date):
        """Get students absent on specific date"""
        pass
    
    @staticmethod
    def generate_attendance_report(klass, start_date, end_date):
        """Generate attendance report for class"""
        pass
