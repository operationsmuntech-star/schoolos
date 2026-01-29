"""
Attendance business logic services - Phase 1
"""
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from backend.attendance.models import AttendanceSession, Attendance, AttendanceException
from backend.core.models import Term


class AttendanceEngine:
    """Core attendance operations"""
    
    @staticmethod
    def create_session(klass, term, date, subject=None, teacher=None):
        """Create new attendance session"""
        session, created = AttendanceSession.objects.get_or_create(
            school=klass.school,
            klass=klass,
            date=date,
            subject=subject,
            defaults={
                'term': term,
                'teacher': teacher,
                'status': 'open'
            }
        )
        return session, created
    
    @staticmethod
    def mark_attendance(session, student, status, remarks='', marked_by=None):
        """Mark student attendance - supports offline"""
        if session.status == 'synced':
            raise ValueError("Cannot modify synced session")
        
        attendance, created = Attendance.objects.update_or_create(
            session=session,
            student=student,
            defaults={
                'status': status,
                'remarks': remarks,
                'marked_by': marked_by,
                'synced': False
            }
        )
        return attendance, created
    
    @staticmethod
    def close_session(session):
        """Close attendance session for marking complete"""
        session.mark_closed()
        return session
    
    @staticmethod
    def bulk_mark_attendance(session, records):
        """Mark multiple attendance records at once
        
        Args:
            session: AttendanceSession
            records: List of dicts with student_id, status, remarks, marked_by
        
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        for record in records:
            attendance, created = Attendance.objects.update_or_create(
                session=session,
                student_id=record['student_id'],
                defaults={
                    'status': record['status'],
                    'remarks': record.get('remarks', ''),
                    'marked_by_id': record.get('marked_by_id'),
                    'synced': False
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return created_count, updated_count


class AttendanceService:
    """Attendance calculation and reporting services"""
    
    @staticmethod
    def get_current_term(school):
        """Get active term for school"""
        return Term.objects.filter(school=school, is_active=True).first()
    
    @staticmethod
    def calculate_attendance_rate(student, term=None, as_percentage=True):
        """Calculate student attendance rate for term
        
        Args:
            student: Student instance
            term: Optional Term filter
            as_percentage: Return as percentage (0-100) or decimal (0-1)
        
        Returns:
            float: Attendance rate
        """
        qs = Attendance.objects.filter(student=student, status='P')
        
        if term:
            qs = qs.filter(session__term=term)
        
        total_sessions = Attendance.objects.filter(student=student)
        if term:
            total_sessions = total_sessions.filter(session__term=term)
        
        total_sessions = total_sessions.count()
        if total_sessions == 0:
            return 0
        
        present_count = qs.count()
        rate = (present_count / total_sessions) * 100 if as_percentage else present_count / total_sessions
        
        return rate
    
    @staticmethod
    def get_absentees(klass, date=None):
        """Get students absent on specific date
        
        Args:
            klass: Class instance
            date: Optional specific date. Defaults to today.
        
        Returns:
            QuerySet of Attendance records with status ABSENT
        """
        if not date:
            date = timezone.now().date()
        
        sessions = AttendanceSession.objects.filter(klass=klass, date=date)
        return Attendance.objects.filter(
            session__in=sessions,
            status='A'
        ).select_related('student', 'session')
    
    @staticmethod
    def get_late_arrivals(klass, date=None):
        """Get students marked late on specific date"""
        if not date:
            date = timezone.now().date()
        
        sessions = AttendanceSession.objects.filter(klass=klass, date=date)
        return Attendance.objects.filter(
            session__in=sessions,
            status='L'
        ).select_related('student', 'session')
    
    @staticmethod
    def get_class_attendance_summary(klass, date=None, term=None):
        """Get attendance summary for class
        
        Returns:
            Dict with attendance statistics
        """
        if not date:
            date = timezone.now().date()
        
        qs = AttendanceSession.objects.filter(klass=klass, date=date)
        if term:
            qs = qs.filter(term=term)
        
        sessions = qs
        attendance_qs = Attendance.objects.filter(session__in=sessions)
        
        stats = attendance_qs.values('status').annotate(count=Count('id')).order_by('status')
        status_map = {s['status']: s['count'] for s in stats}
        
        total = attendance_qs.count()
        
        return {
            'date': date,
            'class': klass.name,
            'total_records': total,
            'present': status_map.get('P', 0),
            'absent': status_map.get('A', 0),
            'late': status_map.get('L', 0),
            'excused': status_map.get('E', 0),
            'present_rate': (status_map.get('P', 0) / total * 100) if total > 0 else 0,
        }
    
    @staticmethod
    def generate_attendance_report(klass, start_date, end_date, term=None):
        """Generate attendance report for class over date range
        
        Returns:
            Dict with report data
        """
        sessions = AttendanceSession.objects.filter(
            klass=klass,
            date__gte=start_date,
            date__lte=end_date
        )
        
        if term:
            sessions = sessions.filter(term=term)
        
        attendance_qs = Attendance.objects.filter(
            session__in=sessions
        ).select_related('student', 'session')
        
        # Group by student
        report = {}
        for record in attendance_qs:
            student = record.student
            if student.id not in report:
                report[student.id] = {
                    'student': student,
                    'admission_number': student.admission_number,
                    'name': student.person.full_name,
                    'total_sessions': 0,
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0,
                    'rate': 0,
                }
            
            report[student.id]['total_sessions'] += 1
            if record.status == 'P':
                report[student.id]['present'] += 1
            elif record.status == 'A':
                report[student.id]['absent'] += 1
            elif record.status == 'L':
                report[student.id]['late'] += 1
            elif record.status == 'E':
                report[student.id]['excused'] += 1
        
        # Calculate rates
        for student_data in report.values():
            if student_data['total_sessions'] > 0:
                student_data['rate'] = (student_data['present'] / student_data['total_sessions']) * 100
        
        return list(report.values())
    
    @staticmethod
    def check_attendance_exceptions(student, date):
        """Check if student has exceptions covering a date
        
        Returns:
            AttendanceException or None
        """
        return AttendanceException.objects.filter(
            student=student,
            start_date__lte=date,
            end_date__gte=date
        ).first()
    
    @staticmethod
    def get_pending_sync_count(school=None):
        """Get count of attendance records pending sync
        
        Args:
            school: Optional school filter
        
        Returns:
            int: Count of records with synced=False
        """
        qs = Attendance.objects.filter(synced=False)
        if school:
            qs = qs.filter(session__school=school)
        return qs.count()
    
    @staticmethod
    def get_unsynced_records(school=None, limit=1000):
        """Get unsynced attendance records for syncing
        
        Args:
            school: Optional school filter
            limit: Maximum records to return
        
        Returns:
            QuerySet of unsynced Attendance records
        """
        qs = Attendance.objects.filter(synced=False).select_related(
            'student', 'session', 'marked_by'
        )
        if school:
            qs = qs.filter(session__school=school)
        
        return qs[:limit]


class SyncService:
    """Sync-ready operations for offline-first reconciliation"""
    
    @staticmethod
    def prepare_for_sync(session_id):
        """Prepare session and its attendance records for sync
        
        Returns:
            Dict with session data and attendance records
        """
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return None
        
        records = Attendance.objects.filter(session=session)
        
        return {
            'session': {
                'id': session.id,
                'local_id': session.local_id,
                'school_id': session.school_id,
                'class_id': session.klass_id,
                'term_id': session.term_id,
                'date': session.date.isoformat(),
                'subject_id': session.subject_id,
                'teacher_id': session.teacher_id,
                'status': session.status,
                'opened_at': session.opened_at.isoformat(),
                'closed_at': session.closed_at.isoformat() if session.closed_at else None,
            },
            'attendance_records': [
                {
                    'id': r.id,
                    'local_id': r.local_id,
                    'student_id': r.student_id,
                    'status': r.status,
                    'remarks': r.remarks,
                    'marked_at': r.marked_at.isoformat(),
                    'marked_by_id': r.marked_by_id,
                }
                for r in records
            ]
        }
    
    @staticmethod
    def handle_sync_conflict(local_record, server_record):
        """Handle conflicts during sync - last write wins
        
        Args:
            local_record: Dict from client
            server_record: Dict from server
        
        Returns:
            Dict: The record that should be kept
        """
        # Parse timestamps
        local_time = local_record.get('marked_at')
        server_time = server_record.get('marked_at')
        
        # Last write wins
        if local_time > server_time:
            return local_record
        return server_record
    
    @staticmethod
    def mark_records_synced(record_ids):
        """Mark multiple records as synced"""
        Attendance.objects.filter(id__in=record_ids).update(
            synced=True,
            last_sync_at=timezone.now()
        )
