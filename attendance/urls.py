from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'students', views.StudentViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'classrooms', views.ClassroomViewSet)
router.register(r'sessions', views.SessionViewSet)
router.register(r'attendance', views.AttendanceRecordViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('scan/<uuid:token>/', views.scan_attendance, name='scan_attendance'),
]
