from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Teacher, Classroom, Session, AttendanceRecord, UserProfile


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['photo_preview', 'student_id', 'name', 'email', 'get_classrooms', 'enrollment_date', 'is_active']
    list_filter = ['is_active', 'enrollment_date', 'classrooms']
    search_fields = ['student_id', 'name', 'email']
    filter_horizontal = ['classrooms']
    ordering = ['name']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('student_id', 'name', 'email', 'phone_number', 'photo')
        }),
        ('Enrollment', {
            'fields': ('classrooms', 'enrollment_date', 'is_active')
        }),
    )
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return format_html('<div style="width: 40px; height: 40px; background: #ccc; border-radius: 50%; display: flex; align-items: center; justify-content: center;"><i class="bi bi-person"></i></div>')
    photo_preview.short_description = 'Photo'
    
    def get_classrooms(self, obj):
        return ", ".join([c.name for c in obj.classrooms.all()[:3]])
    get_classrooms.short_description = 'Classrooms'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'department', 'phone']
    list_filter = ['department']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'department']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'capacity', 'get_student_count', 'location', 'is_active']
    list_filter = ['building', 'is_active']
    search_fields = ['name', 'building', 'location']
    ordering = ['building', 'name']
    
    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = 'Students'



@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'classroom', 'teacher', 'session_date', 'is_active', 'attendance_count', 'created_at']
    list_filter = ['is_active', 'session_date', 'classroom', 'teacher']
    search_fields = ['title', 'description', 'classroom__name', 'teacher__user__first_name']
    readonly_fields = ['qr_token', 'created_at', 'closed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('title', 'description', 'classroom', 'teacher', 'session_date')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at', 'closed_at')
        }),
        ('QR Code', {
            'fields': ('qr_token',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['get_student_photo', 'student', 'session', 'marked_at', 'ip_address']
    list_filter = ['marked_at', 'session__session_date']
    search_fields = ['student__name', 'student__student_id', 'session__title']
    readonly_fields = ['marked_at', 'ip_address', 'user_agent']
    ordering = ['-marked_at']
    
    def get_student_photo(self, obj):
        if obj.student.photo:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%; object-fit: cover;" />', obj.student.photo.url)
        return format_html('<div style="width: 30px; height: 30px; background: #ccc; border-radius: 50%;"></div>')
    get_student_photo.short_description = 'Photo'
    
    def has_add_permission(self, request):
        # Prevent manual addition through admin
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avatar_preview', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['avatar_preview']

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;object-fit:cover;" />', obj.avatar.url)
        return "—"
    avatar_preview.short_description = 'Preview'
