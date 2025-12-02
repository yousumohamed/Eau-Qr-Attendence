from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Additional profile information for any Django user (admin, teacher, student)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.get_username()} Profile"


class Student(models.Model):
    """Student model for tracking attendees"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    classrooms = models.ManyToManyField('Classroom', related_name='students', blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.name}"


class Teacher(models.Model):
    """Teacher model linked to Django User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='teachers/photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Classroom(models.Model):
    """Classroom/Location model"""
    name = models.CharField(max_length=100, unique=True)
    building = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=30)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['building', 'name']

    def __str__(self):
        if self.building:
            return f"{self.building} - {self.name}"
        return self.name


class Session(models.Model):
    """Attendance session with QR code"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_date = models.DateField(default=timezone.now)
    session_start_time = models.TimeField(null=True, blank=True)
    session_end_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['qr_token']),
            models.Index(fields=['session_date']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        # Set expiration time if not set
        if not self.expires_at:
            hours = getattr(settings, 'SESSION_EXPIRY_HOURS', 2)
            self.expires_at = timezone.now() + timedelta(hours=hours)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at or not self.is_active

    def close_session(self):
        """Manually close the session"""
        self.is_active = False
        self.closed_at = timezone.now()
        self.save()

    def attendance_count(self):
        """Get count of students who marked attendance"""
        return self.attendance_records.count()

    def __str__(self):
        return f"{self.title} - {self.session_date} ({self.classroom})"


class AttendanceRecord(models.Model):
    """Individual attendance record"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    marked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-marked_at']
        unique_together = [['session', 'student']]  # Prevent duplicate attendance
        indexes = [
            models.Index(fields=['session', 'student']),
            models.Index(fields=['marked_at']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.session.title} ({self.marked_at.strftime('%Y-%m-%d %H:%M')})"


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Automatically create or ensure a profile exists for each user."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
