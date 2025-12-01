from rest_framework import serializers
from .models import Student, Teacher, Classroom, Session, AttendanceRecord
from django.contrib.auth.models import User


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'student_id', 'name', 'email', 'enrollment_date', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'employee_id', 'full_name', 'username', 'department', 'phone', 'created_at']
        read_only_fields = ['created_at']


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'building', 'capacity', 'location', 'is_active']


class SessionSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    attendance_count = serializers.IntegerField(read_only=True)
    is_expired = serializers.SerializerMethodField()
    qr_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'title', 'description', 'classroom', 'classroom_name',
            'teacher', 'teacher_name', 'session_date', 'created_at',
            'expires_at', 'qr_token', 'is_active', 'closed_at',
            'attendance_count', 'is_expired', 'qr_url'
        ]
        read_only_fields = ['qr_token', 'created_at', 'closed_at', 'attendance_count']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_qr_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/scan/{obj.qr_token}/')
        return f'/scan/{obj.qr_token}/'


class SessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sessions"""
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'description', 'classroom', 'session_date', 'expires_at', 'qr_token']
        read_only_fields = ['id', 'qr_token']
        extra_kwargs = {
            'expires_at': {'required': False}
        }
    
    def create(self, validated_data):
        # Teacher is set from request.user in the view
        return Session.objects.create(**validated_data)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'session_title', 'student', 'student_name',
            'student_id', 'marked_at', 'ip_address'
        ]
        read_only_fields = ['marked_at', 'ip_address']


class MarkAttendanceSerializer(serializers.Serializer):
    """Serializer for marking attendance via QR scan"""
    student_id = serializers.CharField(required=False)
    
    def validate(self, data):
        # If user is not authenticated, student_id is required
        request = self.context.get('request')
        if not request.user.is_authenticated and not data.get('student_id'):
            raise serializers.ValidationError({
                'student_id': 'Student ID is required for unauthenticated users.'
            })
        return data
