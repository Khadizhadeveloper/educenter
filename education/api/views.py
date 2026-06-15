from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from education.models.student import Student
from education.models.mentor import Mentor
from education.models.course import Course
from education.models.group import Group
from education.models.lesson import Lesson
from education.models.schedule import Schedule
from education.models.homework import Homework, HomeworkSubmission
from education.models.grade import Grade
from education.models.attendance import Attendance
from education.models.enrollment import Enrollment
from education.models.notification import Notification
from education.models.kpi import StudentKPI, MentorKPI

from .serializers import (
    StudentSerializer, MentorSerializer, CourseSerializer, GroupSerializer,
    LessonSerializer, ScheduleSerializer, HomeworkSerializer,
    HomeworkSubmissionSerializer, GradeSerializer, AttendanceSerializer,
    EnrollmentSerializer, StudentKPISerializer, MentorKPISerializer,
    NotificationSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'admin'


@extend_schema(tags=['Студенты'])
class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.select_related('user').filter(is_active=True)
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'grade']


@extend_schema(tags=['Менторы'])
class MentorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mentor.objects.select_related('user').all()
    serializer_class = MentorSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Курсы'])
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.select_related('mentor__user').filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @extend_schema(summary='Группы курса')
    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        course = self.get_object()
        groups = Group.objects.filter(course=course, is_active=True)
        return Response(GroupSerializer(groups, many=True).data)

    @extend_schema(summary='Занятия курса')
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        course = self.get_object()
        lessons = Lesson.objects.filter(course=course).order_by('date')
        return Response(LessonSerializer(lessons, many=True).data)

    @extend_schema(summary='Расписание курса')
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        course = self.get_object()
        schedules = Schedule.objects.filter(course=course)
        return Response(ScheduleSerializer(schedules, many=True).data)


@extend_schema(tags=['Группы'])
class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.select_related('course', 'mentor__user').prefetch_related('students__user').filter(is_active=True)
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Расписание'])
class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.select_related('course').all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Занятия'])
class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.select_related('course').order_by('-date')
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'course__name']


@extend_schema(tags=['Домашние задания'])
class HomeworkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Homework.objects.select_related('lesson__course').order_by('-due_date')
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Сдачи ДЗ'])
class HomeworkSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = HomeworkSubmission.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = HomeworkSubmission.objects.select_related(
            'student__user', 'homework__lesson__course'
        )
        if user.role == 'student':
            try:
                return qs.filter(student=user.student_profile)
            except Exception:
                return qs.none()
        if user.role == 'mentor':
            try:
                return qs.filter(homework__lesson__course__mentor=user.mentor_profile)
            except Exception:
                return qs.none()
        return qs


@extend_schema(tags=['Оценки'])
class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Grade.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = Grade.objects.select_related('student__user', 'course')
        if user.role == 'student':
            try:
                return qs.filter(student=user.student_profile)
            except Exception:
                return qs.none()
        return qs


@extend_schema(tags=['Посещаемость'])
class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Attendance.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.select_related('student__user', 'lesson__course')
        if user.role == 'student':
            try:
                return qs.filter(student=user.student_profile)
            except Exception:
                return qs.none()
        return qs


@extend_schema(tags=['Записи на курсы'])
class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Enrollment.objects.select_related('student__user', 'course').filter(is_active=True)
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['KPI'])
class StudentKPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentKPI.objects.select_related('student__user').order_by('-total_kpi')
    serializer_class = StudentKPISerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['KPI'])
class MentorKPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MentorKPI.objects.select_related('mentor__user').order_by('-total_kpi')
    serializer_class = MentorKPISerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Уведомления'])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.none()

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
