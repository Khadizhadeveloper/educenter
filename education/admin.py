from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'avatar', 'date_of_birth', 'address')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):


    list_display = ('get_full_name', 'parent', 'grade', 'enrollment_date', 'is_active')
    list_filter = ('is_active', 'grade', 'enrollment_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    date_hierarchy = 'enrollment_date'

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Имя'


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):


    list_display = ('get_full_name', 'specialization', 'experience_years', 'hire_date')
    list_filter = ('specialization', 'hire_date')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    date_hierarchy = 'hire_date'

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Имя'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):


    list_display = ('name', 'mentor', 'start_date', 'end_date', 'max_students', 'is_active')
    list_filter = ('is_active', 'start_date', 'mentor')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    filter_horizontal = ()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):


    list_display = ('student', 'course', 'enrollment_date', 'is_active')
    list_filter = ('is_active', 'enrollment_date', 'course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'course__name')
    date_hierarchy = 'enrollment_date'


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):


    list_display = ('course', 'weekday', 'start_time', 'end_time', 'room')
    list_filter = ('weekday', 'course')
    search_fields = ('course__name', 'room')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):


    list_display = ('title', 'course', 'date', 'start_time', 'end_time', 'room', 'is_cancelled')
    list_filter = ('is_cancelled', 'date', 'course')
    search_fields = ('title', 'course__name', 'room')
    date_hierarchy = 'date'


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):


    list_display = ('title', 'lesson', 'due_date', 'created_at')
    list_filter = ('due_date', 'created_at', 'lesson__course')
    search_fields = ('title', 'description', 'lesson__course__name')
    date_hierarchy = 'due_date'


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):


    list_display = ('student', 'homework', 'status', 'grade', 'submitted_at')
    list_filter = ('status', 'submitted_at', 'homework__lesson__course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'homework__title')
    date_hierarchy = 'submitted_at'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):


    list_display = ('student', 'lesson', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'lesson__course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'lesson__title')
    date_hierarchy = 'created_at'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):


    list_display = ('student', 'course', 'lesson', 'grade', 'date')
    list_filter = ('grade', 'date', 'course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'course__name')
    date_hierarchy = 'date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):


    list_display = ('title', 'author', 'target_audience', 'is_pinned', 'created_at')
    list_filter = ('target_audience', 'is_pinned', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'