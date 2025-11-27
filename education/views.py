from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *



def home(request):

    announcements = Announcement.objects.filter(target_audience='all')[:5]
    context = {
        'announcements': announcements,
    }
    return render(request, 'home.html', context)



def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')

    return render(request, 'login.html')


def logout_view(request):

    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('home')


def register_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})



@login_required
def dashboard(request):

    user = request.user

    if user.role == 'admin':
        return admin_dashboard(request)
    elif user.role == 'mentor':
        return mentor_dashboard(request)
    elif user.role == 'parent':
        return parent_dashboard(request)
    elif user.role == 'student':
        return student_dashboard(request)

    return render(request, 'dashboard.html')


@login_required
def admin_dashboard(request):

    total_students = Student.objects.filter(is_active=True).count()
    total_mentors = Mentor.objects.count()
    total_courses = Course.objects.filter(is_active=True).count()

    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:10]
    upcoming_lessons = Lesson.objects.filter(date__gte=timezone.now().date()).order_by('date', 'start_time')[:10]

    context = {
        'total_students': total_students,
        'total_mentors': total_mentors,
        'total_courses': total_courses,
        'recent_enrollments': recent_enrollments,
        'upcoming_lessons': upcoming_lessons,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def mentor_dashboard(request):

    try:
        mentor = request.user.mentor_profile
    except:
        messages.error(request, 'Профиль ментора не найден.')
        return redirect('home')

    my_courses = Course.objects.filter(mentor=mentor, is_active=True)
    today_lessons = Lesson.objects.filter(
        course__in=my_courses,
        date=timezone.now().date()
    ).order_by('start_time')

    pending_homework = HomeworkSubmission.objects.filter(
        homework__lesson__course__in=my_courses,
        status='pending'
    ).count()

    context = {
        'mentor': mentor,
        'my_courses': my_courses,
        'today_lessons': today_lessons,
        'pending_homework': pending_homework,
    }
    return render(request, 'mentor_dashboard.html', context)


@login_required
def parent_dashboard(request):

    children = Student.objects.filter(parent=request.user, is_active=True)


    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    upcoming_schedule = []
    for child in children:
        child_courses = child.enrollments.filter(is_active=True).values_list('course', flat=True)
        lessons = Lesson.objects.filter(
            course__in=child_courses,
            date__gte=today,
            date__lte=week_end
        ).order_by('date', 'start_time')

        for lesson in lessons:
            upcoming_schedule.append({
                'child': child,
                'lesson': lesson
            })


    pending_homework = []
    for child in children:
        homework = HomeworkSubmission.objects.filter(
            student=child,
            status='pending'
        ).select_related('homework', 'homework__lesson')
        pending_homework.extend(homework)

    context = {
        'children': children,
        'upcoming_schedule': upcoming_schedule,
        'pending_homework': pending_homework,
    }
    return render(request, 'parent_dashboard.html', context)


@login_required
def student_dashboard(request):

    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Профиль ученика не найден.')
        return redirect('home')

    my_courses = student.enrollments.filter(is_active=True)

    today = timezone.now().date()
    week_end = today + timedelta(days=7)
    upcoming_lessons = Lesson.objects.filter(
        course__in=my_courses.values_list('course', flat=True),
        date__gte=today,
        date__lte=week_end
    ).order_by('date', 'start_time')

    # Домашние задания
    my_homework = HomeworkSubmission.objects.filter(
        student=student
    ).select_related('homework', 'homework__lesson').order_by('-submitted_at')[:10]

    # Оценки
    recent_grades = Grade.objects.filter(student=student).order_by('-date')[:10]

    context = {
        'student': student,
        'my_courses': my_courses,
        'upcoming_lessons': upcoming_lessons,
        'my_homework': my_homework,
        'recent_grades': recent_grades,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def schedule_view(request):

    user = request.user

    if user.role == 'parent':

        children = Student.objects.filter(parent=user, is_active=True)
        courses = Course.objects.filter(
            enrollments__student__in=children,
            is_active=True
        ).distinct()
    elif user.role == 'student':

        student = user.student_profile
        courses = Course.objects.filter(
            enrollments__student=student,
            enrollments__is_active=True
        )
    elif user.role == 'mentor':

        mentor = user.mentor_profile
        courses = Course.objects.filter(mentor=mentor, is_active=True)
    else:

        courses = Course.objects.filter(is_active=True)

    schedules = Schedule.objects.filter(course__in=courses).select_related('course')


    schedule_by_day = {}
    for schedule in schedules:
        day = schedule.get_weekday_display()
        if day not in schedule_by_day:
            schedule_by_day[day] = []
        schedule_by_day[day].append(schedule)

    context = {
        'schedule_by_day': schedule_by_day,
    }
    return render(request, 'schedule.html', context)


@login_required
def homework_list(request):

    user = request.user

    if user.role == 'student':
        student = user.student_profile
        homework = HomeworkSubmission.objects.filter(
            student=student
        ).select_related('homework', 'homework__lesson')
    elif user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        homework = HomeworkSubmission.objects.filter(
            student__in=children
        ).select_related('homework', 'homework__lesson', 'student')
    elif user.role == 'mentor':
        mentor = user.mentor_profile
        homework = HomeworkSubmission.objects.filter(
            homework__lesson__course__mentor=mentor
        ).select_related('homework', 'homework__lesson', 'student')
    else:
        homework = HomeworkSubmission.objects.all().select_related('homework', 'homework__lesson', 'student')

    context = {
        'homework': homework.order_by('-submitted_at'),
    }
    return render(request, 'homework_list.html', context)


@login_required
def homework_submit(request, homework_id):

    homework = get_object_or_404(Homework, id=homework_id)
    student = request.user.student_profile

    if request.method == 'POST':
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = student

            # Проверяем, не опоздал ли
            if timezone.now() > homework.due_date:
                submission.status = 'late'

            submission.save()
            messages.success(request, 'Домашнее задание успешно сдано!')
            return redirect('homework_list')
    else:
        form = HomeworkSubmissionForm()

    context = {
        'homework': homework,
        'form': form,
    }
    return render(request, 'homework_submit.html', context)



@login_required
def course_list(request):
    """Список курсов"""
    courses = Course.objects.filter(is_active=True).select_related('mentor')

    context = {
        'courses': courses,
    }
    return render(request, 'course_list.html', context)


@login_required
def course_detail(request, course_id):

    course = get_object_or_404(Course, id=course_id)
    lessons = Lesson.objects.filter(course=course).order_by('-date')
    enrollments = Enrollment.objects.filter(course=course, is_active=True).select_related('student')

    context = {
        'course': course,
        'lessons': lessons,
        'enrollments': enrollments,
    }
    return render(request, 'course_detail.html', context)



@login_required
def grades_view(request):

    user = request.user

    if user.role == 'student':
        student = user.student_profile
        grades = Grade.objects.filter(student=student).select_related('course', 'lesson')
    elif user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        grades = Grade.objects.filter(student__in=children).select_related('course', 'lesson', 'student')
    else:
        grades = Grade.objects.all().select_related('course', 'lesson', 'student')

    context = {
        'grades': grades.order_by('-date'),
    }
    return render(request, 'grades.html', context)