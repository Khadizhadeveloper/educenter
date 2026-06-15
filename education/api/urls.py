from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, MentorViewSet, CourseViewSet, GroupViewSet,
    ScheduleViewSet, LessonViewSet, HomeworkViewSet, HomeworkSubmissionViewSet,
    GradeViewSet, AttendanceViewSet, EnrollmentViewSet,
    StudentKPIViewSet, MentorKPIViewSet, NotificationViewSet,
)

router = DefaultRouter()
router.register('students',        StudentViewSet,           basename='student')
router.register('mentors',         MentorViewSet,            basename='mentor')
router.register('courses',         CourseViewSet,            basename='course')
router.register('groups',          GroupViewSet,             basename='group')
router.register('schedules',       ScheduleViewSet,          basename='schedule')
router.register('lessons',         LessonViewSet,            basename='lesson')
router.register('homework',        HomeworkViewSet,          basename='homework')
router.register('submissions',     HomeworkSubmissionViewSet, basename='submission')
router.register('grades',          GradeViewSet,             basename='grade')
router.register('attendance',      AttendanceViewSet,        basename='attendance')
router.register('enrollments',     EnrollmentViewSet,        basename='enrollment')
router.register('kpi/students',    StudentKPIViewSet,        basename='student-kpi')
router.register('kpi/mentors',     MentorKPIViewSet,         basename='mentor-kpi')
router.register('notifications',   NotificationViewSet,      basename='notification')

urlpatterns = router.urls
