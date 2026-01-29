"""
Attendance API endpoints - Phase 1 + Multi-Tenant
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from backend.attendance.models import Attendance, AttendanceSession, AttendanceException
from backend.api.serializers import (
    AttendanceSerializer, AttendanceDetailedSerializer,
    AttendanceSessionSerializer, AttendanceSessionDetailedSerializer,
    AttendanceExceptionSerializer, AttendanceSyncSerializer,
    AttendanceReportSerializer, BulkAttendanceSerializer
)
from backend.attendance.services import AttendanceEngine, AttendanceService, SyncService
from backend.core.tenant_permissions import TenantIsolationMixin, IsTenantMember, IsTeacherOfSchool
from backend.core.permissions import IsTeacher, IsSchoolAdmin


class AttendanceViewSet(TenantIsolationMixin, viewsets.ModelViewSet):
    """Attendance record endpoints - Tenant isolated"""
    queryset = Attendance.objects.select_related('session__school', 'student', 'session', 'marked_by')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return AttendanceDetailedSerializer
        return AttendanceSerializer
    
    def get_queryset(self):
        """Filter by user's school - tenant isolation"""
        user = self.request.user
        
        qs = super().get_queryset()  # Already filtered by TenantIsolationMixin
        
        # Additional filter by student if student user
        if hasattr(user, 'person') and hasattr(user.person, 'student'):
            qs = qs.filter(student=user.person.student)
        
        return qs
    
    @action(detail=False, methods=['get'])
    def pending_sync(self, request):
        """Get unsynced attendance records"""
        school_id = request.query_params.get('school_id')
        limit = int(request.query_params.get('limit', 1000))
        
        records = AttendanceService.get_unsynced_records(school_id=school_id, limit=limit)
        serializer = AttendanceDetailedSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_synced(self, request):
        """Mark multiple records as synced"""
        record_ids = request.data.get('record_ids', [])
        if not record_ids:
            return Response({'error': 'No record_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        SyncService.mark_records_synced(record_ids)
        return Response({'success': True, 'synced_count': len(record_ids)})
    
    @action(detail=False, methods=['post'])
    def sync_batch(self, request):
        """Sync batch of attendance records from client"""
        records = request.data.get('records', [])
        session_id = request.data.get('session_id')
        
        if not session_id or not records:
            return Response(
                {'error': 'session_id and records required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created = 0
        updated = 0
        errors = []
        
        for record in records:
            try:
                attendance, is_created = AttendanceEngine.mark_attendance(
                    session=session,
                    student_id=record.get('student_id'),
                    status=record.get('status'),
                    remarks=record.get('remarks', ''),
                    marked_by_id=record.get('marked_by_id')
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'student_id': record.get('student_id'), 'error': str(e)})
        
        return Response({
            'created': created,
            'updated': updated,
            'errors': errors
        })


class AttendanceSessionViewSet(TenantIsolationMixin, viewsets.ModelViewSet):
    """Attendance session management - Tenant isolated"""
    queryset = AttendanceSession.objects.select_related(
        'school', 'klass', 'term', 'subject', 'teacher'
    ).prefetch_related('attendances')
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, IsTeacherOfSchool]
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return AttendanceSessionDetailedSerializer
        return AttendanceSessionSerializer
    
    def get_queryset(self):
        """Filter by user's school and permissions - tenant isolation"""
        user = self.request.user
        
        qs = super().get_queryset()  # Already filtered by TenantIsolationMixin
        
        # Further filter by teacher's classes
        if hasattr(user, 'person') and hasattr(user.person, 'teacher'):
            teacher = user.person.teacher
            qs = qs.filter(teacher=teacher) | qs.filter(klass__form_teacher=teacher)
        
        return qs.order_by('-date')
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close attendance session"""
        session = self.get_object()
        AttendanceEngine.close_session(session)
        return Response({'status': 'closed', 'session': AttendanceSessionSerializer(session).data})
    
    @action(detail=True, methods=['post'])
    def mark_synced(self, request, pk=None):
        """Mark session as synced"""
        session = self.get_object()
        session.mark_synced()
        return Response({'status': 'synced', 'session': AttendanceSessionSerializer(session).data})
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's sessions"""
        today = timezone.now().date()
        school_id = request.query_params.get('school_id')
        
        qs = self.get_queryset().filter(date=today)
        
        if school_id:
            qs = qs.filter(school_id=school_id)
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_sync(self, request):
        """Get sessions pending sync"""
        qs = self.get_queryset().filter(synced=False)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def bulk_mark(self, request, pk=None):
        """Bulk mark attendance for session"""
        session = self.get_object()
        records = request.data.get('records', [])
        
        created, updated = AttendanceEngine.bulk_mark_attendance(session, records)
        
        return Response({
            'created': created,
            'updated': updated,
            'session': AttendanceSessionDetailedSerializer(session).data
        })
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get session attendance summary"""
        session = self.get_object()
        summary = {
            'session_id': session.id,
            'date': session.date,
            'class': str(session.klass),
            'total_students': session.total_students,
            'present': session.present_count,
            'absent': session.absent_count,
            'present_rate': session.get_attendance_percentage('P'),
            'status': session.status,
            'synced': session.synced
        }
        return Response(summary)


class AttendanceExceptionViewSet(viewsets.ModelViewSet):
    """Attendance exception (excused absence) management"""
    queryset = AttendanceException.objects.select_related(
        'student', 'approved_by'
    )
    serializer_class = AttendanceExceptionSerializer
    permission_classes = [IsAuthenticated, IsSchoolAdmin]
    
    def get_queryset(self):
        """Filter by school"""
        school_id = self.request.query_params.get('school_id')
        qs = super().get_queryset()
        
        if school_id:
            qs = qs.filter(student__person__school_id=school_id)
        
        return qs


class AttendanceReportViewSet(viewsets.ViewSet):
    """Attendance reporting endpoints"""
    permission_classes = [IsAuthenticated, IsSchoolAdmin]
    
    @action(detail=False, methods=['get'])
    def class_summary(self, request):
        """Get class attendance summary"""
        class_id = request.query_params.get('class_id')
        date = request.query_params.get('date')
        term_id = request.query_params.get('term_id')
        
        if not class_id:
            return Response(
                {'error': 'class_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from backend.core.models import Class
        try:
            klass = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {'error': 'Class not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        summary = AttendanceService.get_class_attendance_summary(
            klass,
            date=date,
            term=term_id
        )
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def student_rate(self, request):
        """Get student attendance rate"""
        student_id = request.query_params.get('student_id')
        term_id = request.query_params.get('term_id')
        
        if not student_id:
            return Response(
                {'error': 'student_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from backend.people.models import Student
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        rate = AttendanceService.calculate_attendance_rate(
            student,
            term_id=term_id
        )
        return Response({'student_id': student_id, 'attendance_rate': rate})
    
    @action(detail=False, methods=['get'])
    def generate(self, request):
        """Generate attendance report"""
        class_id = request.query_params.get('class_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        term_id = request.query_params.get('term_id')
        
        if not all([class_id, start_date, end_date]):
            return Response(
                {'error': 'class_id, start_date, end_date required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from backend.core.models import Class, Term
        try:
            klass = Class.objects.get(id=class_id)
            term = Term.objects.get(id=term_id) if term_id else None
        except (Class.DoesNotExist, Term.DoesNotExist):
            return Response(
                {'error': 'Class or Term not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        report = AttendanceService.generate_attendance_report(
            klass,
            start_date,
            end_date,
            term=term
        )
        serializer = AttendanceReportSerializer(report, many=True)
        return Response(serializer.data)
