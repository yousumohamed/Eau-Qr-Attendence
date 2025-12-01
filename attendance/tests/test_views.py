from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from attendance.models import Student, Teacher, Classroom, Session, AttendanceRecord
import json


class SessionAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='teacher1', password='pass123', is_staff=True)
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id="EMP001",
            department="Computer Science"
        )
        self.classroom = Classroom.objects.create(name="Room 101", capacity=30)
        self.client.login(username='teacher1', password='pass123')
    
    def test_create_session(self):
        data = {
            'title': 'Test Session',
            'description': 'Test Description',
            'classroom': self.classroom.id,
            'session_date': timezone.now().date().isoformat()
        }
        response = self.client.post(
            '/api/sessions/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('qr_token', response.json())
    
    def test_create_session_requires_auth(self):
        self.client.logout()
        data = {
            'title': 'Test Session',
            'classroom': self.classroom.id,
            'session_date': timezone.now().date().isoformat()
        }
        response = self.client.post(
            '/api/sessions/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ScanAttendanceTest(TestCase):
    def setUp(self):
        self.client = Client()
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
    
    def test_scan_valid_token(self):
        response = self.client.get(f'/scan/{self.session.qr_token}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.session.title)
    
    def test_scan_invalid_token(self):
        import uuid
        fake_token = uuid.uuid4()
        response = self.client.get(f'/scan/{fake_token}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid session token')
    
    def test_mark_attendance(self):
        response = self.client.post(
            f'/scan/{self.session.qr_token}/',
            {'student_id': self.student.student_id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify attendance was created
        attendance = AttendanceRecord.objects.filter(
            session=self.session,
            student=self.student
        )
        self.assertTrue(attendance.exists())
    
    def test_duplicate_attendance_prevention(self):
        # Mark attendance first time
        response = self.client.post(
            f'/scan/{self.session.qr_token}/',
            {'student_id': self.student.student_id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to mark again - should fail
        response = self.client.post(
            f'/scan/{self.session.qr_token}/',
            {'student_id': self.student.student_id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already marked', response.json()['error'].lower())
    
    def test_expired_session_scan(self):
        # Expire the session
        self.session.expires_at = timezone.now() - timezone.timedelta(hours=1)
        self.session.save()
        
        response = self.client.post(
            f'/scan/{self.session.qr_token}/',
            {'student_id': self.student.student_id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', response.json()['error'].lower())
    
    def test_invalid_student_id(self):
        response = self.client.post(
            f'/scan/{self.session.qr_token}/',
            {'student_id': 'INVALID_ID'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CSVExportTest(TestCase):
    def setUp(self):
        self.client = Client()
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
        
        # Create some attendance records
        for i in range(3):
            student = Student.objects.create(
                student_id=f"STU{i:03d}",
                name=f"Student {i}",
                email=f"student{i}@example.com"
            )
            AttendanceRecord.objects.create(
                session=self.session,
                student=student
            )
        
        self.client.login(username='teacher1', password='pass123')
    
    def test_csv_export(self):
        response = self.client.get('/api/attendance/export_csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Session Title', content)
        self.assertIn('Student ID', content)
        self.assertIn('STU000', content)
    
    def test_csv_export_with_filters(self):
        response = self.client.get(
            f'/api/attendance/export_csv/?session={self.session.id}'
        )
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        # Header + 3 records + empty line
        self.assertEqual(len([l for l in lines if l.strip()]), 4)
