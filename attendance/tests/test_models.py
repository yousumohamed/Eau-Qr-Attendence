from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from attendance.models import Student, Teacher, Classroom, Session, AttendanceRecord


class StudentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_id="STU001",
            name="John Doe",
            email="john@example.com"
        )
    
    def test_student_creation(self):
        self.assertEqual(self.student.student_id, "STU001")
        self.assertEqual(self.student.name, "John Doe")
        self.assertTrue(self.student.is_active)
    
    def test_student_str(self):
        self.assertEqual(str(self.student), "STU001 - John Doe")


class SessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teacher1', password='pass123')
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id="EMP001",
            department="Computer Science"
        )
        self.classroom = Classroom.objects.create(
            name="Room 101",
            capacity=30
        )
        self.session = Session.objects.create(
            classroom=self.classroom,
            teacher=self.teacher,
            title="Morning Lecture",
            session_date=timezone.now().date()
        )
    
    def test_session_creation(self):
        self.assertIsNotNone(self.session.qr_token)
        self.assertTrue(self.session.is_active)
        self.assertIsNotNone(self.session.expires_at)
    
    def test_session_expiration(self):
        # Test active session
        self.assertFalse(self.session.is_expired())
        
        # Test expired session
        self.session.expires_at = timezone.now() - timedelta(hours=1)
        self.session.save()
        self.assertTrue(self.session.is_expired())
    
    def test_session_close(self):
        self.session.close_session()
        self.assertFalse(self.session.is_active)
        self.assertIsNotNone(self.session.closed_at)
    
    def test_qr_token_unique(self):
        session2 = Session.objects.create(
            classroom=self.classroom,
            teacher=self.teacher,
            title="Afternoon Lecture",
            session_date=timezone.now().date()
        )
        self.assertNotEqual(self.session.qr_token, session2.qr_token)


class AttendanceRecordModelTest(TestCase):
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
    
    def test_attendance_creation(self):
        attendance = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            ip_address="127.0.0.1"
        )
        self.assertEqual(attendance.student, self.student)
        self.assertEqual(attendance.session, self.session)
    
    def test_duplicate_attendance_prevention(self):
        # Create first attendance record
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.student
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(
                session=self.session,
                student=self.student
            )
    
    def test_attendance_count(self):
        # Create multiple students
        for i in range(10, 15):
            student = Student.objects.create(
                student_id=f"STU{i:03d}",
                name=f"Student {i}",
                email=f"student{i}@example.com"
            )
            AttendanceRecord.objects.create(
                session=self.session,
                student=student
            )
        
        self.assertEqual(self.session.attendance_count(), 5)
