from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count
import logging

from .models import (
    NotificationPreference, Notification, SMSLog, EmailLog, NotificationTemplate
)
from .serializers import (
    NotificationPreferenceSerializer, NotificationSerializer, SMSLogSerializer,
    EmailLogSerializer, NotificationTemplateSerializer
)
from .services import NotificationService, SMSService, EmailService

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """User-specific notification preferences"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get current user's notification preferences"""
        try:
            prefs = NotificationPreference.objects.get(parent=request.user)
            serializer = NotificationPreferenceSerializer(prefs)
            return Response(serializer.data)
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            prefs = NotificationPreference.objects.create(parent=request.user)
            serializer = NotificationPreferenceSerializer(prefs)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update notification preferences"""
        try:
            prefs = NotificationPreference.objects.get(parent=request.user)
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(parent=request.user)
        
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def test_sms(self, request):
        """Send test SMS to verify phone number"""
        try:
            prefs = NotificationPreference.objects.get(parent=request.user)
            phone = request.data.get('phone_number') or prefs.phone_number
            
            if not phone:
                return Response(
                    {'error': 'No phone number provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            sms_log = SMSLog.objects.create(
                phone_number=phone,
                message='Test SMS from MunTech. Please confirm this is your number.',
                provider='test'
            )
            
            return Response({
                'status': 'SMS test queued',
                'phone_number': phone,
                'sms_log_id': sms_log.id
            })
        except NotificationPreference.DoesNotExist:
            return Response(
                {'error': 'Notification preferences not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationViewSet(viewsets.ModelViewSet):
    """List and manage notifications for current user"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message', 'event_type']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show notifications for current user"""
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail='id', methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'marked_as_read': count})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'unread': queryset.filter(is_read=False).count(),
            'by_event_type': dict(
                queryset.values('event_type').annotate(count=Count('id')).values_list('event_type', 'count')
            ),
            'by_date': {
                'today': queryset.filter(created_at__date=timezone.now().date()).count(),
                'this_week': queryset.filter(
                    created_at__date__gte=timezone.now().date() - timezone.timedelta(days=7)
                ).count(),
                'this_month': queryset.filter(
                    created_at__date__month=timezone.now().month,
                    created_at__date__year=timezone.now().year
                ).count(),
            }
        }
        
        return Response(stats)


class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View SMS notification logs"""
    serializer_class = SMSLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'message', 'provider_message_id']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show SMS logs for notifications sent to current user"""
        return SMSLog.objects.filter(
            notification__recipient=self.request.user
        )
    
    @action(detail='id', methods=['post'])
    def retry(self, request, pk=None):
        """Retry sending failed SMS"""
        sms_log = self.get_object()
        
        if not sms_log.can_retry():
            return Response(
                {'error': 'Cannot retry this SMS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queue for retry
        result = SMSService.send_via_provider(sms_log)
        
        if result['success']:
            return Response({'status': 'Retry queued'})
        else:
            return Response(
                {'error': result.get('error_message', 'Unknown error')},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View email notification logs"""
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['recipient_email', 'subject', 'provider_message_id']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show email logs for notifications sent to current user"""
        return EmailLog.objects.filter(
            notification__recipient=self.request.user
        )
    
    @action(detail='id', methods=['post'])
    def retry(self, request, pk=None):
        """Retry sending failed email"""
        email_log = self.get_object()
        
        if not email_log.can_retry():
            return Response(
                {'error': 'Cannot retry this email'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queue for retry
        result = EmailService.send_via_provider(email_log)
        
        if result['success']:
            return Response({'status': 'Retry queued'})
        else:
            return Response(
                {'error': result.get('error_message', 'Unknown error')},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """View notification templates (read-only for users, admin can edit)"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['event_type', 'title', 'school__name']
    ordering_fields = ['event_type', 'created_at']
    ordering = ['event_type']
    
    def get_queryset(self):
        """Show system templates and school-specific templates"""
        user = self.request.user
        if hasattr(user, 'school'):
            return NotificationTemplate.objects.filter(
                Q(school__isnull=True) | Q(school=user.school),
                is_active=True
            )
        return NotificationTemplate.objects.filter(
            school__isnull=True,
            is_active=True
        )
