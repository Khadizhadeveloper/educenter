from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from datetime import datetime, timedelta
from .forms import *
from django.utils import timezone
from .models.enrollment import Enrollment

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_mentor(user):
    return user.is_authenticated and user.role == 'mentor'


def home(request):
    announcements = Announcement.objects.filter(target_audience='all')[:5]
    return render(request, 'home.html', {'announcements': announcements})




def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

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
@user_passes_test(is_mentor)
def mentor_dashboard(request):
    try:
        mentor = request.user.mentor_profile
    except Exception:
        messages.error(request, 'Профиль ментора не найден.')
        return redirect('home')

    my_courses = Course.objects.filter(mentor=mentor, is_active=True)
    today_lessons = Lesson.objects.filter(
        course__in=my_courses, date=timezone.now().date()
    ).order_by('start_time')
    pending_homework = HomeworkSubmission.objects.filter(
        homework__lesson__course__in=my_courses, status='pending'
    ).count()

    context = {
        'mentor': mentor,
        'my_courses': my_courses,
        'today_lessons': today_lessons,
        'pending_homework': pending_homework,
    }
    return render(request, 'mentor_dashboard.html', context)



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
def parent_dashboard(request):
    children = Student.objects.filter(parent=request.user, is_active=True)
    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    upcoming_schedule = []
    for child in children:
        child_courses = child.enrollments.filter(is_active=True).values_list('course', flat=True)
        lessons = Lesson.objects.filter(
            course__in=child_courses, date__gte=today, date__lte=week_end
        ).order_by('date', 'start_time')
        for lesson in lessons:
            upcoming_schedule.append({'child': child, 'lesson': lesson})

    pending_homework = []
    for child in children:
        hw = HomeworkSubmission.objects.filter(
            student=child, status='pending'
        ).select_related('homework', 'homework__lesson')
        pending_homework.extend(hw)

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
    except Exception:
        messages.error(request, 'Профиль ученика не найден.')
        return redirect('home')

    my_courses = student.enrollments.filter(is_active=True)
    today = timezone.now().date()
    week_end = today + timedelta(days=7)
    upcoming_lessons = Lesson.objects.filter(
        course__in=my_courses.values_list('course', flat=True),
        date__gte=today, date__lte=week_end
    ).order_by('date', 'start_time')
    my_homework = HomeworkSubmission.objects.filter(
        student=student
    ).select_related('homework', 'homework__lesson').order_by('-submitted_at')[:10]
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
@user_passes_test(is_admin, login_url='dashboard')
def admin_user_list(request):
    users = User.objects.all().order_by('role', 'last_name')
    return render(request, 'admin/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_create_user(request):
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()

            if user.role == 'mentor':
                Mentor.objects.get_or_create(user=user, defaults={'specialization': ''})
                messages.success(request, f'Пользователь создан. Заполните профиль ментора.')
                return redirect('admin_mentor_profile', user_id=user.id)

            elif user.role == 'student':
                Student.objects.get_or_create(
                    user=user,
                    defaults={'grade': '', 'parent': None}
                )

            messages.success(request, f'Пользователь {user.get_full_name()} успешно создан.')
            return redirect('admin_user_list')
    else:
        form = AdminCreateUserForm()

    return render(request, 'admin/create_user.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_assign_role(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = AssignRoleForm(request.POST, instance=target_user)
        if form.is_valid():
            old_role = target_user.role
            new_role = form.cleaned_data['role']

            if old_role == 'mentor' and new_role != 'mentor':
                Mentor.objects.filter(user=target_user).delete()

            elif old_role == 'student' and new_role != 'student':
                Student.objects.filter(user=target_user).delete()


            user = form.save()

            if new_role == 'mentor' and old_role != 'mentor':
                Mentor.objects.get_or_create(user=user, defaults={'specialization': ''})
                messages.success(request, 'Роль обновлена. Заполните профиль ментора.')
                return redirect('admin_mentor_profile', user_id=user.id)

            elif new_role == 'student' and old_role != 'student':
                # Создаём базовый профиль ученика
                Student.objects.get_or_create(
                    user=user,
                    defaults={'grade': '', 'parent': None}
                )

            messages.success(
                request,
                f'Роль {user.get_full_name()} изменена на «{user.get_role_display()}».'
            )
            return redirect('admin_user_list')
    else:
        form = AssignRoleForm(instance=target_user)

    return render(request, 'admin/assign_role.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_mentor_profile(request, user_id):

    target_user = get_object_or_404(User, id=user_id, role='mentor')
    mentor, _ = Mentor.objects.get_or_create(user=target_user, defaults={'specialization': ''})

    if request.method == 'POST':
        form = MentorProfileForm(request.POST, request.FILES, instance=mentor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Профиль ментора {target_user.get_full_name()} сохранён.')
            return redirect('admin_user_list')
    else:
        form = MentorProfileForm(instance=mentor)

    return render(request, 'admin/mentor_profile.html', {
        'form': form,
        'target_user': target_user,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard')
def admin_delete_user(request, user_id):

    target_user = get_object_or_404(User, id=user_id)


    if target_user == request.user:
        messages.error(request, 'Нельзя удалить собственный аккаунт.')
        return redirect('admin_user_list')

    if request.method == 'POST':
        name = target_user.get_full_name()
        target_user.delete()
        messages.success(request, f'Пользователь {name} удалён.')
        return redirect('admin_user_list')

    return render(request, 'admin/confirm_delete.html', {'target_user': target_user})




@login_required
def schedule_view(request):
    user = request.user

    if user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        courses = Course.objects.filter(
            enrollments__student__in=children, is_active=True
        ).distinct()
    elif user.role == 'student':
        student = user.student_profile
        courses = Course.objects.filter(
            enrollments__student=student, enrollments__is_active=True
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

    return render(request, 'schedule.html', {'schedule_by_day': schedule_by_day})


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
        homework = HomeworkSubmission.objects.all().select_related(
            'homework', 'homework__lesson', 'student'
        )

    return render(request, 'homework_list.html', {
        'homework': homework.order_by('-submitted_at')
    })


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
            if timezone.now() > homework.due_date:
                submission.status = 'late'
            submission.save()
            messages.success(request, 'Домашнее задание успешно сдано!')
            return redirect('homework_list')
    else:
        form = HomeworkSubmissionForm()

    return render(request, 'homework_submit.html', {'homework': homework, 'form': form})


@login_required
def course_list(request):
    courses = Course.objects.filter(is_active=True).select_related('mentor')
    return render(request, 'course_list.html', {'courses': courses})


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = Lesson.objects.filter(course=course).order_by('-date')
    enrollments = Enrollment.objects.filter(course=course, is_active=True).select_related('student')
    return render(request, 'course_detail.html', {
        'course': course,
        'lessons': lessons,
        'enrollments': enrollments,
    })


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

    return render(request, 'grades.html', {'grades': grades.order_by('-date')})