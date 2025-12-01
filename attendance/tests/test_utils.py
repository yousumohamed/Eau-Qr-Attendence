from django.test import TestCase
from attendance.utils import (
    generate_qr_code, validate_session_token, mark_attendance,
    get_student_by_id, get_client_ip
)
from attendance.models import Student, Teacher, Classroom, Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import RequestFactory


class QRCodeGenerationTest(TestCase):
    def test_generate_qr_code(self):
        url = "http://example.com/scan/test-token/"
        qr_buffer = generate_qr_code(url)
        
        self.assertIsNotNone(qr_buffer)
        self.assertTrue(qr_buffer.tell() == 0)  # Buffer is at start
        
        # Check that it's a valid image buffer
        qr_buffer.seek(0, 2)  # Seek to end
        size = qr_buffer.tell()
        self.assertGreater(size, 0)


class SessionValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id="EMP001",
            department="Computer Science"
        )
        self.classroom = Classroom.objects.create(name="Room 101", capacity=30)
        self.session = Session.objects.create(
            classroom=self.classroom,
            teacher=self.teacher,
            title="Test Session",
            session_date=timezone.now().date()
        )
    
    def test_validate_valid_token(self):
        is_valid, result = validate_session_token(str(self.session.qr_token))
        self.assertTrue(is_valid)
        self.assertEqual(result, self.session)
    
    def test_validate_invalid_token(self):
        import uuid
        is_valid, result = validate_session_token(str(uuid.uuid4()))
        self.assertFalse(is_valid)
        self.assertIn('Invalid', result)
    
    def test_validate_expired_token(self):
        self.session.expires_at = timezone.now() - timezone.timedelta(hours=1)
        self.session.save()
        
        is_valid, result = validate_session_token(str(self.session.qr_token))
        self.assertFalse(is_valid)
        self.assertIn('expired', result.lower())
    
    def test_validate_closed_session(self):
        self.session.is_active = False
        self.session.save()
        
        is_valid, result = validate_session_token(str(self.session.qr_token))
        self.assertFalse(is_valid)
        self.assertIn('closed', result.lower())


class AttendanceMarkingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id="EMP001",
            department="Computer Science"
        )
        self.classroom = Classroom.objects.create(name="Room 101", capacity=30)
        self.session = Session.objects.create(
            classroom=self.classroom,
            teacher=self.teacher,
            title="Test Session",
            session_date=timezone.now().date()
        )
        self.student = Student.objects.create(
            student_id="STU001",
            name="John Doe",
            email="john@example.com"
        )
    
    def test_mark_attendance_success(self):
        success, result = mark_attendance(
            self.session,
            self.student,
            ip_address="127.0.0.1"
        )
        self.assertTrue(success)
        self.assertEqual(result.student, self.student)
        self.assertEqual(result.session, self.session)
    
    def test_mark_duplicate_attendance(self):
        # Mark first time
        success, result = mark_attendance(self.session, self.student)
        self.assertTrue(success)
        
        # Try to mark again
        success, result = mark_attendance(self.session, self.student)
        self.assertFalse(success)
        self.assertIn('already marked', result.lower())


class StudentLookupTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_id="STU001",
            name="John Doe",
            email="john@example.com"
        )
    
    def test_get_student_by_valid_id(self):
        found, result = get_student_by_id("STU001")
        self.assertTrue(found)
        self.assertEqual(result, self.student)
    
    def test_get_student_by_invalid_id(self):
        found, result = get_student_by_id("INVALID")
        self.assertFalse(found)
        self.assertIn('not found', result.lower())
    
    def test_get_inactive_student(self):
        self.student.is_active = False
        self.student.save()
        
        found, result = get_student_by_id("STU001")
        self.assertFalse(found)


class ClientIPTest(TestCase):
    def test_get_client_ip_direct(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_forwarded(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')
