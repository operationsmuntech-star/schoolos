"""
DRF Serializers - Phase 1
"""
from rest_framework import serializers
from backend.attendance.models import Attendance, AttendanceSession, AttendanceException
from backend.people.models import Student, Teacher
from backend.core.models import Class
from backend.users.models import User


class StudentBasicSerializer(serializers.ModelSerializer):
    """Basic student info"""
    name = serializers.CharField(source='person.full_name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'admission_number', 'name']


class TeacherBasicSerializer(serializers.ModelSerializer):
    """Basic teacher info"""
    name = serializers.CharField(source='person.full_name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'teacher_code', 'name']


class ClassBasicSerializer(serializers.ModelSerializer):
    """Basic class info"""
    class Meta:
        model = Class
        fields = ['id', 'name', 'level', 'stream']


class AttendanceSerializer(serializers.ModelSerializer):
    """Attendance record serializer"""
    student = StudentBasicSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'session', 'student', 'student_id', 'status', 
            'status_display', 'remarks', 'marked_at', 'marked_by', 
            'synced', 'local_id'
        ]
        read_only_fields = ['marked_at', 'id']


class AttendanceDetailedSerializer(serializers.ModelSerializer):
    """Detailed attendance with all metadata"""
    student = StudentBasicSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    marked_by = TeacherBasicSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'session', 'student', 'student_id', 'status', 
            'status_display', 'remarks', 'marked_at', 'updated_at',
            'marked_by', 'synced', 'last_sync_at', 'local_id'
        ]
        read_only_fields = ['marked_at', 'updated_at', 'last_sync_at', 'id']


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Attendance session serializer"""
    teacher = TeacherBasicSerializer(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    klass = ClassBasicSerializer(read_only=True)
    class_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'school', 'klass', 'class_id', 'term', 'date', 
            'subject', 'teacher', 'teacher_id', 'status', 'status_display',
            'opened_at', 'closed_at', 'synced_at', 'synced', 'local_id'
        ]
        read_only_fields = ['opened_at', 'closed_at', 'synced_at', 'id']


class AttendanceSessionDetailedSerializer(serializers.ModelSerializer):
    """Detailed session with attendance records"""
    attendances = AttendanceSerializer(many=True, read_only=True)
    teacher = TeacherBasicSerializer(read_only=True)
    klass = ClassBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_students = serializers.IntegerField(read_only=True)
    present_count = serializers.IntegerField(read_only=True)
    absent_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'school', 'klass', 'term', 'date', 'subject', 'teacher',
            'status', 'status_display', 'opened_at', 'closed_at', 'synced_at',
            'total_students', 'present_count', 'absent_count',
            'attendances', 'synced'
        ]
        read_only_fields = ['opened_at', 'closed_at', 'synced_at', 'id']


class AttendanceExceptionSerializer(serializers.ModelSerializer):
    """Attendance exception serializer"""
    student = StudentBasicSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = AttendanceException
        fields = [
            'id', 'student', 'student_id', 'category', 'category_display',
            'start_date', 'end_date', 'reason', 'approved_by', 'created_at'
        ]
        read_only_fields = ['created_at', 'id']


class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer for bulk attendance marking"""
    session_id = serializers.IntegerField()
    records = AttendanceSerializer(many=True)


class AttendanceSyncSerializer(serializers.Serializer):
    """Serializer for sync data from offline client"""
    local_id = serializers.CharField(required=False, allow_blank=True)
    session_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    status = serializers.CharField(max_length=1)
    remarks = serializers.CharField(required=False, allow_blank=True)
    marked_at = serializers.DateTimeField()


class AttendanceReportSerializer(serializers.Serializer):
    """Attendance report data"""
    student_id = serializers.IntegerField()
    admission_number = serializers.CharField()
    name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    excused = serializers.IntegerField()
    rate = serializers.FloatField()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for auth responses"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'school_id']
