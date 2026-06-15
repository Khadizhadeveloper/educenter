from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Attendance, HomeworkSubmission, Grade
from .models.kpi import StudentKPI, MentorKPI
from .models.test_system import TestAttempt
from .models.enrollment import Enrollment
from .models.group import Group
from .models.notification import Notification
from .models.user import User


def _refresh_student(student):
    kpi, _ = StudentKPI.objects.get_or_create(student=student)
    kpi.recalculate()


def _refresh_mentor(mentor):
    if mentor:
        kpi, _ = MentorKPI.objects.get_or_create(mentor=mentor)
        kpi.recalculate()


@receiver(post_save, sender=Attendance)
@receiver(post_delete, sender=Attendance)
def on_attendance_change(sender, instance, **kwargs):
    _refresh_student(instance.student)
    _refresh_mentor(instance.lesson.course.mentor)


@receiver(post_save, sender=HomeworkSubmission)
@receiver(post_delete, sender=HomeworkSubmission)
def on_homework_change(sender, instance, **kwargs):
    _refresh_student(instance.student)
    _refresh_mentor(instance.homework.lesson.course.mentor)


@receiver(post_save, sender=Grade)
@receiver(post_delete, sender=Grade)
def on_grade_change(sender, instance, **kwargs):
    _refresh_student(instance.student)
    _refresh_mentor(instance.course.mentor)


@receiver(post_save, sender=TestAttempt)
def on_test_attempt_finish(sender, instance, **kwargs):
    if instance.finished_at:
        _refresh_student(instance.student)
        try:
            _refresh_mentor(instance.test.topic.course.mentor)
        except Exception:
            pass


def _notify_admins_and_mentor(message, notification_type, mentor=None):
    admins = User.objects.filter(role='admin')
    for admin in admins:
        Notification.objects.create(recipient=admin, message=message, notification_type=notification_type)
    if mentor:
        Notification.objects.create(recipient=mentor.user, message=message, notification_type=notification_type)


@receiver(post_save, sender=Enrollment)
def auto_assign_to_group(sender, instance, created, **kwargs):
    if not created:
        return

    student = instance.student
    course = instance.course

    # Найти группу у которой студентов < max_students
    available_group = None
    for g in Group.objects.filter(course=course, is_active=True):
        if g.students.count() < g.max_students:
            available_group = g
            break

    if available_group:
        available_group.students.add(student)
        # Проверить — не заполнилась ли только что
        if available_group.students.count() >= available_group.max_students:
            msg = (
                f'Группа «{available_group.name}» (курс: {course.name}) заполнена — '
                f'{available_group.max_students} студентов.'
            )
            _notify_admins_and_mentor(msg, 'group_full', mentor=available_group.mentor)
    else:
        # Все группы заполнены — создать новую автоматически
        existing_count = Group.objects.filter(course=course).count()
        new_name = f'{course.name[:10]}-{existing_count + 1}'
        new_group = Group.objects.create(
            name=new_name,
            course=course,
            mentor=course.mentor,
            max_students=10,
        )
        new_group.students.add(student)
        msg = (
            f'Все группы курса «{course.name}» заполнены. '
            f'Автоматически создана новая группа «{new_name}».'
        )
        _notify_admins_and_mentor(msg, 'group_created', mentor=course.mentor)
