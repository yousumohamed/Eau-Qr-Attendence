import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import IntegrityError
from .models import Session, AttendanceRecord, Student
import csv
from django.http import HttpResponse


def generate_qr_code(url, size=10, border=2):
    """
    Generate a QR code image for the given URL.
    
    Args:
        url: The URL to encode in the QR code
        size: Size of the QR code (default 10)
        border: Border size (default 2)
    
    Returns:
        BytesIO object containing the QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def validate_session_token(token):
    """
    Validate if a session token is valid and active.
    
    Args:
        token: UUID token string
    
    Returns:
        tuple: (is_valid, session_or_error_message)
    """
    try:
        session = Session.objects.get(qr_token=token)
        
        if not session.is_active:
            return False, "Session has been closed."
        
        if session.is_expired():
            return False, "Session has expired."
        
        return True, session
    
    except Session.DoesNotExist:
        return False, "Invalid session token."


def mark_attendance(session, student, ip_address=None, user_agent=None):
    """
    Mark attendance for a student in a session.
    Prevents duplicate attendance records.
    
    Args:
        session: Session object
        student: Student object
        ip_address: IP address of the request (optional)
        user_agent: User agent string (optional)
    
    Returns:
        tuple: (success, attendance_record_or_error_message)
    """
    try:
        # Check if already marked
        existing = AttendanceRecord.objects.filter(
            session=session,
            student=student
        ).first()
        
        if existing:
            return False, f"Attendance already marked at {existing.marked_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create attendance record
        attendance = AttendanceRecord.objects.create(
            session=session,
            student=student,
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        return True, attendance
    
    except IntegrityError:
        # Handle race condition where duplicate might be created
        return False, "Attendance already marked."
    except Exception as e:
        return False, f"Error marking attendance: {str(e)}"


def get_student_by_id(student_id):
    """
    Get student by student_id.
    
    Args:
        student_id: Student ID string
    
    Returns:
        tuple: (found, student_or_error_message)
    """
    try:
        student = Student.objects.get(student_id=student_id, is_active=True)
        return True, student
    except Student.DoesNotExist:
        return False, "Student not found or inactive."


def export_attendance_to_csv(queryset, filename='attendance_report.csv'):
    """
    Export attendance records to CSV.
    
    Args:
        queryset: QuerySet of AttendanceRecord objects
        filename: Name of the CSV file
    
    Returns:
        HttpResponse with CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Session Title',
        'Session Date',
        'Classroom',
        'Student ID',
        'Student Name',
        'Student Email',
        'Marked At',
        'IP Address'
    ])
    
    # Write data
    for record in queryset.select_related('session', 'student', 'session__classroom'):
        writer.writerow([
            record.session.title,
            record.session.session_date.strftime('%Y-%m-%d'),
            record.session.classroom.name,
            record.student.student_id,
            record.student.name,
            record.student.email,
            record.marked_at.strftime('%Y-%m-%d %H:%M:%S'),
            record.ip_address or 'N/A'
        ])
    
    return response


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
    
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
