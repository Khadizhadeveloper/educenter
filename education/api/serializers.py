from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from education.models.user import User
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone']


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username  = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'username', 'full_name', 'grade', 'enrollment_date', 'is_active']


class MentorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username  = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Mentor
        fields = ['id', 'username', 'full_name', 'specialization', 'experience_years', 'hire_date']


class CourseSerializer(serializers.ModelSerializer):
    mentor_name = serializers.CharField(source='mentor.user.get_full_name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'mentor_name', 'duration_weeks',
                  'max_students', 'start_date', 'end_date', 'is_active']


class GroupSerializer(serializers.ModelSerializer):
    course_name  = serializers.CharField(source='course.name', read_only=True)
    mentor_name  = serializers.CharField(source='mentor.user.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    students     = StudentSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'course_name', 'mentor_name',
                  'max_students', 'student_count', 'students', 'is_active']

    @extend_schema_field(serializers.IntegerField())
    def get_student_count(self, obj):
        return obj.students.count()


class ScheduleSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'course_name', 'weekday', 'weekday_display', 'start_time', 'end_time', 'room']


class LessonSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'course_name', 'title', 'description', 'date',
                  'start_time', 'end_time', 'room', 'is_cancelled']


class HomeworkSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='lesson.course.name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Homework
        fields = ['id', 'course_name', 'lesson_title', 'title', 'description', 'due_date']


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)

    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'student_name', 'homework_title', 'content',
                  'status', 'grade', 'feedback', 'submitted_at', 'checked_at']


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    course_name  = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Grade
        fields = ['id', 'student_name', 'course_name', 'grade', 'comment', 'date']


class AttendanceSerializer(serializers.ModelSerializer):
    student_name    = serializers.CharField(source='student.user.get_full_name', read_only=True)
    lesson_title    = serializers.CharField(source='lesson.title', read_only=True)
    status_display  = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student_name', 'lesson_title', 'status', 'status_display', 'notes']


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    course_name  = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student_name', 'course_name', 'enrollment_date', 'is_active']


class StudentKPISerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    kpi_label    = serializers.CharField(read_only=True)

    class Meta:
        model = StudentKPI
        fields = ['id', 'student_name', 'attendance_score', 'homework_score',
                  'grade_score', 'total_kpi', 'total_lessons', 'attended_lessons',
                  'kpi_label', 'updated_at']


class MentorKPISerializer(serializers.ModelSerializer):
    mentor_name = serializers.CharField(source='mentor.user.get_full_name', read_only=True)
    kpi_label   = serializers.CharField(read_only=True)

    class Meta:
        model = MentorKPI
        fields = ['id', 'mentor_name', 'avg_student_kpi', 'avg_attendance',
                  'homework_completion_rate', 'total_kpi', 'kpi_label', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'is_read', 'created_at']
