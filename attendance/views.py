from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F, IntegerField, ExpressionWrapper
from datetime import datetime, timedelta

from .models import Student, Teacher, Classroom, Session, AttendanceRecord
from .serializers import (
    StudentSerializer, TeacherSerializer, ClassroomSerializer,
    SessionSerializer, SessionCreateSerializer, AttendanceRecordSerializer,
    MarkAttendanceSerializer
)
from .permissions import IsTeacherOrAdmin, IsAuthenticatedOrPublicScan
from .utils import (
    generate_qr_code, validate_session_token, mark_attendance,
    get_student_by_id, export_attendance_to_csv, get_client_ip
)


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing students"""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class TeacherViewSet(viewsets.ModelViewSet):
    """ViewSet for managing teachers"""
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]


class ClassroomViewSet(viewsets.ModelViewSet):
    """ViewSet for managing classrooms"""
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class SessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance sessions"""
    queryset = Session.objects.all()
    permission_classes = [IsTeacherOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SessionCreateSerializer
        return SessionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by classroom
        classroom_id = self.request.query_params.get('classroom')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.select_related('teacher', 'classroom').annotate(
            attendance_count=Count('attendance_records')
        )
    
    def perform_create(self, serializer):
        # Get or create teacher profile for the user
        teacher = None
        if hasattr(self.request.user, 'teacher_profile'):
            teacher = self.request.user.teacher_profile
        elif self.request.user.is_staff:
            # For admin users, try to get first teacher or create one
            teacher = Teacher.objects.first()
            if not teacher:
                teacher = Teacher.objects.create(
                    user=self.request.user,
                    employee_id=f"ADMIN-{self.request.user.id}",
                    department="Administration"
                )
        
        serializer.save(teacher=teacher)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Manually close a session"""
        session = self.get_object()
        session.close_session()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Get QR code image for session"""
        session = self.get_object()
        
        # Generate QR code URL
        qr_url = request.build_absolute_uri(f'/scan/{session.qr_token}/')
        
        # Generate QR code image
        qr_image = generate_qr_code(qr_url)
        
        from django.http import HttpResponse
        return HttpResponse(qr_image.getvalue(), content_type='image/png')
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get attendance records for a session"""
        session = self.get_object()
        records = session.attendance_records.all()
        serializer = AttendanceRecordSerializer(records, many=True)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def scan_attendance(request, token):
    """
    Public endpoint for scanning QR code and marking attendance.
    GET: Display scan page
    POST: Mark attendance
    """
    # Validate session token
    is_valid, result = validate_session_token(token)
    
    if not is_valid:
        if request.method == 'GET':
            return render(request, 'scan_page.html', {
                'error': result,
                'token': token
            })
        return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
    
    session = result
    
    if request.method == 'GET':
        # Render scan page
        return render(request, 'scan_page.html', {
            'session': session,
            'token': token
        })
    
    # POST - Mark attendance
    serializer = MarkAttendanceSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Get student
    student = None
    student_id = serializer.validated_data.get('student_id')
    
    if student_id:
        # Manual student ID entry
        found, result = get_student_by_id(student_id)
        if not found:
            return Response({'error': result}, status=status.HTTP_404_NOT_FOUND)
        student = result
    elif request.user.is_authenticated:
        # Try to get student from authenticated user
        try:
            student = request.user.student_profile
        except:
            return Response({
                'error': 'No student profile found for your account. Please enter your student ID.'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'error': 'Please provide your student ID.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Mark attendance
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    success, result = mark_attendance(session, student, ip_address, user_agent)
    
    if not success:
        return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
    
    # Success
    attendance_record = result
    return Response({
        'success': True,
        'message': 'Attendance marked successfully!',
        'student': student.name,
        'session': session.title,
        'marked_at': attendance_record.marked_at
    }, status=status.HTTP_201_CREATED)


class AttendanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing attendance records"""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by session
        session_id = self.request.query_params.get('session')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(marked_at__gte=start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(marked_at__lt=end_datetime)
        
        return queryset.select_related('session', 'student', 'session__classroom')
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export attendance records to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Generate filename with date range
        filename = 'attendance_report'
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            filename = f'attendance_{start_date}_to_{end_date}.csv'
        elif start_date:
            filename = f'attendance_from_{start_date}.csv'
        
        return export_attendance_to_csv(queryset, filename)


# Frontend Template Views

def dashboard(request):
    """Main dashboard - redirects based on user type"""
    if request.user.is_authenticated:
        # Check if user is a student first
        try:
            student = request.user.student_profile
            return student_dashboard(request)
        except:
            pass
        
        # Check if user is a teacher or admin
        if request.user.is_staff:
            return teacher_dashboard(request)
        
        try:
            teacher = request.user.teacher_profile
            return teacher_dashboard(request)
        except:
            pass
    
    # Default landing page
    return render(request, 'dashboard.html')


def student_dashboard(request):
    """Student dashboard showing stats and history"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    try:
        student = request.user.student_profile
    except:
        return render(request, 'dashboard.html', {'error': 'No student profile found.'})

    # Get attendance records
    records = AttendanceRecord.objects.filter(student=student).select_related(
        'session', 'session__classroom', 'session__teacher__user'
    ).order_by('-marked_at')

    # Get active sessions from student's enrolled classrooms
    active_sessions = Session.objects.filter(
        classroom__in=student.classrooms.all(),
        is_active=True
    ).select_related('classroom', 'teacher__user').order_by('-created_at')

    # Calculate stats
    total_attendance = records.count()
    total_sessions = Session.objects.filter(
        classroom__in=student.classrooms.all()
    ).distinct().count()

    attendance_percentage = 0
    if total_sessions > 0:
        attendance_percentage = round((total_attendance / total_sessions) * 100)

    context = {
        'student': student,
        'recent_records': records[:10],
        'active_sessions': active_sessions,
        'total_attendance': total_attendance,
        'attendance_percentage': attendance_percentage,
        'total_sessions': total_sessions,
    }
    return render(request, 'student_dashboard.html', context)


def teacher_dashboard(request):
    """Teacher dashboard showing sessions"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Get teacher sessions with stats
    sessions = Session.objects.all().annotate(
        attendance_count=Count('attendance_records', distinct=True),
        classroom_size=Count('classroom__students', distinct=True),
    ).annotate(
        absent_count=ExpressionWrapper(
            F('classroom_size') - F('attendance_count'),
            output_field=IntegerField()
        )
    ).order_by('-created_at')
    
    # Filter by teacher if not admin
    if not request.user.is_staff and hasattr(request.user, 'teacher_profile'):
        sessions = sessions.filter(teacher=request.user.teacher_profile)
    
    # Get classrooms for session creation
    classrooms = Classroom.objects.filter(is_active=True)

    # Aggregate stats for dashboard
    teacher_classrooms = classrooms
    if not request.user.is_staff and hasattr(request.user, 'teacher_profile'):
        # Only classrooms where this teacher has (or had) sessions
        teacher_classrooms = Classroom.objects.filter(
            sessions__teacher=request.user.teacher_profile,
            is_active=True
        ).distinct()

    total_students_in_classes = Student.objects.filter(
        classrooms__in=teacher_classrooms,
        is_active=True
    ).distinct().count()

    todays_sessions_count = sessions.filter(
        session_date=datetime.today().date()
    ).count()

    total_sessions_count = sessions.count()

    context = {
        'sessions': sessions[:20],
        'active_sessions': sessions.filter(is_active=True),
        'classrooms': classrooms,
        'total_students_in_classes': total_students_in_classes,
        'todays_sessions_count': todays_sessions_count,
        'total_sessions_count': total_sessions_count,
    }

    return render(request, 'teacher_dashboard.html', context)


def session_qr_view(request, pk):
    """Display QR code for a session"""
    session = get_object_or_404(Session, pk=pk)
    
    # Check permission
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    if not request.user.is_staff:
        if not hasattr(request.user, 'teacher_profile') or session.teacher != request.user.teacher_profile:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to view this session.")
    
    # Generate QR URL
    qr_url = request.build_absolute_uri(f'/scan/{session.qr_token}/')
    
    # Get attendance records
    attendance_records = session.attendance_records.all().select_related('student')

    # Students who belong to this classroom but have not yet marked attendance
    absent_students = session.classroom.students.exclude(
        attendance_records__session=session
    ).distinct()

    context = {
        'session': session,
        'qr_url': qr_url,
        'attendance_records': attendance_records,
        'attendance_count': attendance_records.count(),
        'absent_students': absent_students,
        'total_class_size': session.classroom.students.count(),
        'absent_count': absent_students.count(),
    }
    
    return render(request, 'session_qr.html', context)


def reports_view(request):
    """Attendance reports with filtering"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Get filter parameters
    session_id = request.GET.get('session')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    student_id = request.GET.get('student')
    
    # Build queryset
    records = AttendanceRecord.objects.all().select_related(
        'session', 'student', 'session__classroom'
    )
    
    # Apply filters
    if session_id:
        records = records.filter(session_id=session_id)
    
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        records = records.filter(marked_at__gte=start_datetime)
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        records = records.filter(marked_at__lt=end_datetime)
    
    if student_id:
        records = records.filter(student_id=student_id)
    
    # Filter by teacher if not admin
    if not request.user.is_staff and hasattr(request.user, 'teacher_profile'):
        records = records.filter(session__teacher=request.user.teacher_profile)
    
    # Get sessions and students for filter dropdowns
    sessions_qs = Session.objects.all()
    if not request.user.is_staff and hasattr(request.user, 'teacher_profile'):
        sessions_qs = sessions_qs.filter(teacher=request.user.teacher_profile)
    sessions = sessions_qs.order_by('-created_at')[:50]
    
    students = Student.objects.filter(is_active=True).order_by('name')
    
    context = {
        'records': records[:100],
        'sessions': sessions,
        'students': students,
        'filters': {
            'session_id': session_id,
            'start_date': start_date,
            'end_date': end_date,
            'student_id': student_id,
        }
    }
    
    return render(request, 'reports.html', context)


def change_password_view(request):
    """Allow users to change their password"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        from django.contrib import messages
        
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            # Change password
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('dashboard')
    
    return render(request, 'change_password.html')


def teacher_view_students(request):
    """Teacher can view all students in their classrooms"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Get teacher's classrooms
    if request.user.is_staff:
        # Admin sees all
        classrooms = Classroom.objects.filter(is_active=True).prefetch_related('students')
    elif hasattr(request.user, 'teacher_profile'):
        # Teacher sees their classrooms
        teacher = request.user.teacher_profile
        classrooms = Classroom.objects.filter(
            sessions__teacher=teacher,
            is_active=True
        ).distinct().prefetch_related('students')
    else:
        classrooms = []
    
    context = {
        'classrooms': classrooms,
    }
    
    return render(request, 'teacher_students.html', context)

