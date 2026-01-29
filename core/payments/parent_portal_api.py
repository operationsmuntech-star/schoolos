"""
Parent Portal API - Read-only endpoints for parents to view student data

Parents can access:
- Student fees and invoices
- Payment history
- Attendance records
- Exam results
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.shortcuts import get_object_or_404
import logging

from core.fees.models import Invoice, FeePayment, Arrears
from core.fees.serializers import InvoiceDetailSerializer, PaymentSerializer
from core.attendance.models import Attendance, AttendanceReport
from core.examinations.models import Marks
from core.users.models import Student, School
from core.notifications.models import Notification

logger = logging.getLogger(__name__)


class StudentFeeSerializer:
    """Serializer for parent viewing student fees"""
    pass


class ParentStandardPagination:
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsParent(permissions.BasePermission):
    """
    Permission: User is a parent and can only access their child's data
    """
    def has_permission(self, request, view):
        # Check if user has a related student (is a parent)
        return hasattr(request.user, 'children') or hasattr(request.user, 'student_set')

    def has_object_permission(self, request, view, obj):
        # Parent can only view their own child
        if hasattr(request.user, 'children'):
            # If parent has children relationship
            return obj.user == request.user or obj in request.user.children.all()
        elif hasattr(request.user, 'student_set'):
            # If user is a student viewing own data
            return obj.user == request.user
        return False


class StudentFeesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parents to view student fees
    
    GET /parent/students/{student_id}/fees/ - List all invoices
    GET /parent/students/{student_id}/fees/{invoice_id}/ - View invoice detail
    GET /parent/students/{student_id}/fees/summary/ - Fee summary stats
    """
    
    serializer_class = InvoiceDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'term']
    ordering_fields = ['issue_date', 'due_date', 'total_amount']
    ordering = ['-issue_date']
    
    def get_queryset(self):
        """
        Parent can only see invoices for their child
        """
        student_id = self.kwargs.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        
        # Verify parent has access to this student
        if hasattr(self.request.user, 'children'):
            if student not in self.request.user.children.all():
                return Invoice.objects.none()
        elif student.user != self.request.user:
            return Invoice.objects.none()
        
        return Invoice.objects.filter(student=student).select_related(
            'student', 'school', 'term', 'created_by'
        ).prefetch_related('fee_payments')
    
    @action(detail=False, methods=['get'])
    def summary(self, request, student_id=None):
        """
        Get fee summary statistics for student
        
        Returns:
        - total_invoiced: Total amount across all invoices
        - total_paid: Total amount paid
        - total_outstanding: Total amount still owed
        - avg_payment_method: Most common payment method
        - invoice_count: Total number of invoices
        - paid_count: Invoices marked as fully paid
        """
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total_invoiced=Sum('total_amount'),
            total_paid=Sum('amount_paid'),
            invoice_count=Count('id'),
            paid_count=Count('id', filter=Q(balance=0))
        )
        
        if not stats['total_invoiced']:
            stats['total_invoiced'] = 0
            stats['total_paid'] = 0
        
        stats['total_outstanding'] = stats['total_invoiced'] - stats['total_paid']
        stats['outstanding_percentage'] = round(
            (stats['total_outstanding'] / stats['total_invoiced'] * 100) 
            if stats['total_invoiced'] > 0 else 0, 2
        )
        
        return Response(stats)


class StudentPaymentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parents to view payment history
    
    GET /parent/students/{student_id}/payments/ - List all payments
    GET /parent/students/{student_id}/payments/{payment_id}/ - View payment detail
    GET /parent/students/{student_id}/payments/stats/ - Payment statistics
    """
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['payment_method', 'status']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    pagination_class = ParentStandardPagination
    
    def get_queryset(self):
        """
        Parent can only see payments for their child's invoices
        """
        student_id = self.kwargs.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        
        # Verify parent has access
        if hasattr(self.request.user, 'children'):
            if student not in self.request.user.children.all():
                return FeePayment.objects.none()
        elif student.user != self.request.user:
            return FeePayment.objects.none()
        
        return FeePayment.objects.filter(
            invoice__student=student,
            status='completed'
        ).select_related('invoice', 'recorded_by')
    
    @action(detail=False, methods=['get'])
    def stats(self, request, student_id=None):
        """
        Get payment statistics
        
        Returns:
        - total_payments: Count of payments made
        - total_amount: Total paid
        - avg_payment: Average payment amount
        - payment_methods: Breakdown by method
        """
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total_payments=Count('id'),
            total_amount=Sum('amount'),
            avg_payment=Avg('amount')
        )
        
        # Breakdown by payment method
        payment_methods = queryset.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        
        stats['payment_methods'] = [
            {
                'method': pm['payment_method'],
                'count': pm['count'],
                'total': str(pm['total']) if pm['total'] else '0.00'
            }
            for pm in payment_methods
        ]
        
        return Response(stats)


class StudentAttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parents to view attendance
    
    GET /parent/students/{student_id}/attendance/ - List attendance records
    GET /parent/students/{student_id}/attendance/summary/ - Attendance percentage
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['date', 'present']
    ordering = ['-date']
    pagination_class = ParentStandardPagination
    
    def get_queryset(self):
        """Parent can only see their child's attendance"""
        student_id = self.kwargs.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        
        # Verify access
        if hasattr(self.request.user, 'children'):
            if student not in self.request.user.children.all():
                return Attendance.objects.none()
        elif student.user != self.request.user:
            return Attendance.objects.none()
        
        return Attendance.objects.filter(student=student).select_related('student', 'class_assigned')
    
    def get_serializer_class(self):
        # Simple serializer for attendance
        from rest_framework import serializers
        
        class AttendanceSerializer(serializers.ModelSerializer):
            class Meta:
                model = Attendance
                fields = ['id', 'date', 'present', 'class_assigned']
        
        return AttendanceSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request, student_id=None):
        """
        Get attendance summary
        
        Returns:
        - total_days: Total days in system
        - present_days: Days marked present
        - absent_days: Days marked absent
        - attendance_percentage: Percentage
        - current_term_attendance: This term only
        """
        queryset = self.get_queryset()
        
        summary = queryset.aggregate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(present=True)),
            absent_days=Count('id', filter=Q(present=False))
        )
        
        if summary['total_days'] > 0:
            summary['attendance_percentage'] = round(
                (summary['present_days'] / summary['total_days'] * 100), 2
            )
        else:
            summary['attendance_percentage'] = 0
        
        return Response(summary)


class StudentExamResultsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parents to view exam results
    
    GET /parent/students/{student_id}/exams/ - List exam results
    GET /parent/students/{student_id}/exams/summary/ - Performance summary
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exam', 'subject']
    ordering = ['-exam__date']
    pagination_class = ParentStandardPagination
    
    def get_queryset(self):
        """Parent can only see their child's exam results"""
        student_id = self.kwargs.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        
        # Verify access
        if hasattr(self.request.user, 'children'):
            if student not in self.request.user.children.all():
                return Marks.objects.none()
        elif student.user != self.request.user:
            return Marks.objects.none()
        
        return Marks.objects.filter(student=student).select_related(
            'student', 'exam', 'subject'
        )
    
    def get_serializer_class(self):
        # Simple serializer for exam results
        from rest_framework import serializers
        
        class ExamResultSerializer(serializers.ModelSerializer):
            exam_name = serializers.CharField(source='exam.name', read_only=True)
            subject_name = serializers.CharField(source='subject.name', read_only=True)
            
            class Meta:
                model = Marks
                fields = ['id', 'exam', 'exam_name', 'subject', 'subject_name', 'score', 'grade', 'comment']
        
        return ExamResultSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request, student_id=None):
        """
        Get exam performance summary
        
        Returns:
        - avg_score: Average across all exams
        - best_subject: Subject with highest score
        - weakest_subject: Subject with lowest score
        - exam_count: Total number of exams
        - grade_distribution: Count by grade
        """
        queryset = self.get_queryset()
        
        summary = queryset.aggregate(
            exam_count=Count('exam_id', distinct=True),
            avg_score=Avg('score'),
            max_score=Max('score'),
            min_score=Min('score')
        )
        
        # Grade distribution
        grade_dist = queryset.values('grade').annotate(count=Count('id')).order_by('grade')
        summary['grade_distribution'] = list(grade_dist)
        
        return Response(summary)


class StudentNotificationsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parents to view notifications
    
    GET /parent/students/{student_id}/notifications/ - List unread notifications
    GET /parent/notifications/unread-count/ - Count of unread
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event_type', 'is_read']
    ordering = ['-created_at']
    pagination_class = ParentStandardPagination
    
    def get_queryset(self):
        """Parent can only see their own notifications"""
        return Notification.objects.filter(recipient=self.request.user).select_related(
            'student', 'invoice'
        )
    
    def get_serializer_class(self):
        from rest_framework import serializers
        from core.notifications.serializers import NotificationSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})


def get_student_or_child(request, student_id):
    """
    Helper: Get student and verify parent has access
    Returns Student or raises 404
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Verify access
    if hasattr(request.user, 'children'):
        if student not in request.user.children.all():
            raise PermissionError("Parent does not have access to this student")
    elif hasattr(request.user, 'student') and request.user.student != student:
        # Student viewing own data
        raise PermissionError("Student can only view own data")
    elif student.user != request.user:
        raise PermissionError("User does not have access to this student")
    
    return student
