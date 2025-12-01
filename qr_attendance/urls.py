from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from attendance import views as attendance_views

# Override the default admin login
admin.site.login = auth_views.LoginView.as_view(template_name='login.html')

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('admin/login/', auth_views.LoginView.as_view(template_name='login.html'), name='admin_login'),
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'),
    path('', attendance_views.dashboard, name='dashboard'),
    path('teacher/', attendance_views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', attendance_views.student_dashboard, name='student_dashboard'),
    path('session/<int:pk>/qr/', attendance_views.session_qr_view, name='session_qr'),
    path('reports/', attendance_views.reports_view, name='reports'),
    path('change-password/', attendance_views.change_password_view, name='change_password'),
    path('teacher/students/', attendance_views.teacher_view_students, name='teacher_students'),
    path('', include('attendance.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
