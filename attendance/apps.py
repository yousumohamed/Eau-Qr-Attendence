from django.apps import AppConfig
from django.contrib.auth import get_user_model


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        """Attach helper attributes to the User model for admin avatars."""
        User = get_user_model()

        def _admin_avatar(self):
            profile = getattr(self, 'profile', None)
            if profile and profile.avatar:
                return profile.avatar.url
            teacher = getattr(self, 'teacher_profile', None)
            if teacher and teacher.photo:
                return teacher.photo.url
            student = getattr(self, 'student_profile', None)
            if student and student.photo:
                return student.photo.url
            return None

        if not hasattr(User, 'admin_avatar'):
            User.add_to_class('admin_avatar', property(_admin_avatar))
