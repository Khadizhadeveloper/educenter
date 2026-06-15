from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from datetime import datetime, timedelta
from .forms import *
from django.utils import timezone
from .models.enrollment import Enrollment
from .models.attendance import Attendance
from .models.kpi import StudentKPI, MentorKPI
from .models.test_system import Topic, Test, Question, Answer, TestAttempt, StudentAnswer
from .models.notification import Notification
from .models.group import Group

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_mentor(user):
    return user.is_authenticated and user.role == 'mentor'

def is_parent(user):
    return user.is_authenticated and user.role == 'parent'

def is_student(user):
    return user.is_authenticated and user.role == 'student'


def home(request):
    from .models.news import News
    announcements = Announcement.objects.filter(target_audience='all')[:5]
    news_list = News.objects.filter(is_published=True)[:6]
    return render(request, 'home.html', {'announcements': announcements, 'news_list': news_list})




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
            if user.role == 'student':
                Student.objects.get_or_create(user=user, defaults={'grade': '', 'parent': None})
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
    today = timezone.now().date()
    today_lessons = Lesson.objects.filter(
        course__in=my_courses, date=today
    ).order_by('start_time')
    pending_submissions = HomeworkSubmission.objects.filter(
        homework__lesson__course__in=my_courses, status__in=['pending', 'late']
    ).select_related('student__user', 'homework__lesson__course').order_by('submitted_at')
    pending_homework = pending_submissions.count()

    mentor_kpi, _ = MentorKPI.objects.get_or_create(mentor=mentor)

    enrolled_students = Student.objects.filter(
        enrollments__course__in=my_courses, enrollments__is_active=True
    ).distinct()
    student_kpis = []
    for s in enrolled_students:
        kpi, _ = StudentKPI.objects.get_or_create(student=s)
        student_kpis.append(kpi)
    student_kpis.sort(key=lambda k: k.total_kpi, reverse=True)

    # Last 7 days lessons with attendance stats
    week_ago = today - timedelta(days=7)
    recent_lessons = Lesson.objects.filter(
        course__in=my_courses,
        date__gte=week_ago,
        date__lte=today,
        is_cancelled=False,
    ).select_related('course').order_by('-date', '-start_time')

    lessons_with_attendance = []
    for lesson in recent_lessons:
        enrolled_count = Enrollment.objects.filter(
            course=lesson.course, is_active=True
        ).count()
        marked_count = Attendance.objects.filter(lesson=lesson).count()
        present_count = Attendance.objects.filter(
            lesson=lesson, status__in=['present', 'late', 'excused']
        ).count()
        attendance_pct = round(present_count / enrolled_count * 100) if enrolled_count else 0
        lessons_with_attendance.append({
            'lesson': lesson,
            'enrolled': enrolled_count,
            'marked': marked_count,
            'present': present_count,
            'attendance_pct': attendance_pct,
            'is_marked': marked_count > 0,
        })

    my_groups = Group.objects.filter(
        mentor=mentor, is_active=True
    ).prefetch_related('students__user').select_related('course')

    context = {
        'mentor': mentor,
        'my_courses': my_courses,
        'my_groups': my_groups,
        'today_lessons': today_lessons,
        'pending_homework': pending_homework,
        'pending_submissions': pending_submissions[:20],
        'mentor_kpi': mentor_kpi,
        'student_kpis': student_kpis,
        'lessons_with_attendance': lessons_with_attendance,
    }
    return render(request, 'mentor_dashboard.html', context)


@login_required
@user_passes_test(is_mentor)
def mentor_create_homework(request):
    # Страница для добавления ДЗ ментором без доступа к админке
    try:
        mentor = request.user.mentor_profile
    except Exception:
        messages.error(request, 'Профиль ментора не найден.')
        return redirect('home')

    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        # Ограничиваем выбор уроков только уроками курсов данного ментора
        if 'lesson' in form.fields:
            form.fields['lesson'].queryset = Lesson.objects.filter(course__mentor=mentor)
        if form.is_valid():
            homework = form.save()
            messages.success(request, 'Домашнее задание успешно добавлено.')
            return redirect('homework_list')
    else:
        form = HomeworkForm()
        if 'lesson' in form.fields:
            form.fields['lesson'].queryset = Lesson.objects.filter(course__mentor=mentor)

    return render(request, 'mentor/homework_create.html', {'form': form})


@login_required
@user_passes_test(is_mentor)
def mentor_create_lesson(request):
    # Создание занятия ментором без доступа к админке
    try:
        mentor = request.user.mentor_profile
    except Exception:
        messages.error(request, 'Профиль ментора не найден.')
        return redirect('home')

    if request.method == 'POST':
        form = LessonForm(request.POST)
        # Разрешаем выбирать только свои курсы
        if 'course' in form.fields:
            form.fields['course'].queryset = Course.objects.filter(mentor=mentor, is_active=True)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, 'Занятие успешно создано.')
            return redirect('course_detail', course_id=lesson.course.id)
    else:
        form = LessonForm()
        if 'course' in form.fields:
            form.fields['course'].queryset = Course.objects.filter(mentor=mentor, is_active=True)

    return render(request, 'mentor/lesson_create.html', {'form': form})


@login_required
@user_passes_test(is_mentor)
def mentor_give_grade(request):
    # Выставление оценки ментором без доступа к админке
    try:
        mentor = request.user.mentor_profile
    except Exception:
        messages.error(request, 'Профиль ментора не найден.')
        return redirect('home')

    if request.method == 'POST':
        form = GradeForm(request.POST)
        # Ограничиваем выбор значениями в зоне ответственности ментора
        if 'course' in form.fields:
            form.fields['course'].queryset = Course.objects.filter(mentor=mentor, is_active=True)
        if 'lesson' in form.fields:
            form.fields['lesson'].queryset = Lesson.objects.filter(course__mentor=mentor)
        if 'student' in form.fields:
            form.fields['student'].queryset = Student.objects.filter(
                enrollments__course__mentor=mentor,
                enrollments__is_active=True
            ).distinct()

        if form.is_valid():
            grade_obj = form.save(commit=False)
            # Дополнительные проверки согласованности
            if grade_obj.lesson and grade_obj.lesson.course != grade_obj.course:
                form.add_error('lesson', 'Выбранный урок не относится к выбранному курсу.')
            # Проверка, что студент записан на курс
            is_enrolled = Enrollment.objects.filter(
                student=grade_obj.student,
                course=grade_obj.course,
                is_active=True
            ).exists()
            if not is_enrolled:
                form.add_error('student', 'Студент не записан на выбранный курс.')

            if not form.errors:
                grade_obj.save()
                messages.success(request, 'Оценка успешно выставлена.')
                return redirect('grades')
    else:
        form = GradeForm()
        if 'course' in form.fields:
            form.fields['course'].queryset = Course.objects.filter(mentor=mentor, is_active=True)
        if 'lesson' in form.fields:
            form.fields['lesson'].queryset = Lesson.objects.filter(course__mentor=mentor)
        if 'student' in form.fields:
            form.fields['student'].queryset = Student.objects.filter(
                enrollments__course__mentor=mentor,
                enrollments__is_active=True
            ).distinct()

    return render(request, 'mentor/grade_create.html', {'form': form})


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
@user_passes_test(is_parent)
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
@user_passes_test(is_student)
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
    recent_grades = Grade.objects.filter(student=student).order_by('-date')[:10]

    student_kpi, _ = StudentKPI.objects.get_or_create(student=student)

    # Назначенные ДЗ по активным курсам
    course_ids = my_courses.values_list('course_id', flat=True)
    hw_assignments = Homework.objects.filter(
        lesson__course_id__in=course_ids
    ).select_related('lesson', 'lesson__course').order_by('due_date')
    submissions_map = {
        s.homework_id: s
        for s in HomeworkSubmission.objects.filter(student=student, homework__in=hw_assignments)
    }
    my_homework = [
        {'homework': hw, 'submission': submissions_map.get(hw.id)}
        for hw in hw_assignments
    ]
    pending_hw_count = sum(1 for item in my_homework if item['submission'] is None)

    context = {
        'student': student,
        'my_courses': my_courses,
        'upcoming_lessons': upcoming_lessons,
        'my_homework': my_homework,
        'pending_hw_count': pending_hw_count,
        'recent_grades': recent_grades,
        'kpi': student_kpi,
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
        try:
            student = user.student_profile
        except Exception:
            messages.error(request, 'Профиль ученика не найден.')
            return redirect('home')
        courses = Course.objects.filter(
            enrollments__student=student, enrollments__is_active=True
        )
    elif user.role == 'mentor':
        try:
            mentor = user.mentor_profile
        except Exception:
            messages.error(request, 'Профиль ментора не найден.')
            return redirect('home')
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
        # Для ученика показываем ВСЕ задания по его активным курсам,
        # вместе со статусом его отправки (если уже сдавал)
        try:
            student = user.student_profile
        except Exception:
            messages.error(request, 'Профиль ученика не найден.')
            return redirect('home')

        course_ids = student.enrollments.filter(is_active=True).values_list('course_id', flat=True)
        assignments = Homework.objects.filter(
            lesson__course_id__in=course_ids
        ).select_related('lesson', 'lesson__course').order_by('-due_date')

        submissions = HomeworkSubmission.objects.filter(
            student=student,
            homework__in=assignments
        ).select_related('homework')
        submissions_by_hw = {s.homework_id: s for s in submissions}

        combined = [
            {
                'homework': hw,
                'submission': submissions_by_hw.get(hw.id)
            }
            for hw in assignments
        ]
        return render(request, 'homework_list.html', {
            'student_assignments': combined
        })

    elif user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        homework = HomeworkSubmission.objects.filter(
            student__in=children
        ).select_related('homework', 'homework__lesson', 'student')
    elif user.role == 'mentor':
        from .models.enrollment import Enrollment as _Enr
        mentor = user.mentor_profile
        assignments = Homework.objects.filter(
            lesson__course__mentor=mentor
        ).select_related('lesson', 'lesson__course').order_by('-due_date')

        mentor_assignments = []
        for hw in assignments:
            enrolled_count = _Enr.objects.filter(
                course=hw.lesson.course, is_active=True
            ).count()
            submitted_count = HomeworkSubmission.objects.filter(homework=hw).count()
            pending_count   = HomeworkSubmission.objects.filter(homework=hw, status='pending').count()
            mentor_assignments.append({
                'homework':       hw,
                'enrolled':       enrolled_count,
                'submitted':      submitted_count,
                'pending':        pending_count,
            })

        return render(request, 'homework_list.html', {
            'mentor_assignments': mentor_assignments,
            'now': timezone.now(),
        })
    else:
        homework = HomeworkSubmission.objects.all().select_related(
            'homework', 'homework__lesson', 'student'
        )

    return render(request, 'homework_list.html', {
        'homework': homework.order_by('-submitted_at')
    })


@login_required
@user_passes_test(is_student)
def homework_submit(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    student = request.user.student_profile

    # Проверяем, что студент записан на курс данного задания
    is_enrolled = Enrollment.objects.filter(
        student=student,
        course=homework.lesson.course,
        is_active=True
    ).exists()
    if not is_enrolled:
        messages.error(request, 'Вы не записаны на курс этого задания.')
        return redirect('homework_list')

    # Проверяем, не сдавал ли студент это задание ранее
    if HomeworkSubmission.objects.filter(homework=homework, student=student).exists():
        messages.error(request, 'Вы уже отправили это задание.')
        return redirect('homework_list')

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
        try:
            student = user.student_profile
        except Exception:
            messages.error(request, 'Профиль ученика не найден.')
            return redirect('home')
        grades = Grade.objects.filter(student=student).select_related('course', 'lesson')
    elif user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        grades = Grade.objects.filter(student__in=children).select_related('course', 'lesson', 'student')
    else:
        grades = Grade.objects.all().select_related('course', 'lesson', 'student')

    grades = grades.order_by('-date')
    from django.db.models import Avg, Max
    stats = grades.aggregate(avg=Avg('grade'), best=Max('grade'))
    excellent_count = grades.filter(grade__gte=8).count()
    good_count      = grades.filter(grade__gte=5, grade__lt=8).count()

    return render(request, 'grades.html', {
        'grades':          grades,
        'avg_grade':       round(stats['avg'], 1) if stats['avg'] else None,
        'best_grade':      stats['best'],
        'excellent_count': excellent_count,
        'good_count':      good_count,
    })


# ── Attendance views ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_mentor)
def mentor_attendance(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Security: only the lesson's course mentor can mark attendance
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if lesson.course.mentor != mentor:
        messages.error(request, 'У вас нет доступа к этому занятию.')
        return redirect('mentor_dashboard')

    enrollments = Enrollment.objects.filter(
        course=lesson.course, is_active=True
    ).select_related('student__user')

    # Build dict of existing records  {student_id: Attendance}
    existing = {
        a.student_id: a
        for a in Attendance.objects.filter(lesson=lesson)
    }

    if request.method == 'POST':
        saved = 0
        for enrollment in enrollments:
            student = enrollment.student
            status = request.POST.get(f'status_{student.id}', 'absent')
            notes  = request.POST.get(f'notes_{student.id}', '')
            obj, _ = Attendance.objects.update_or_create(
                lesson=lesson, student=student,
                defaults={'status': status, 'notes': notes},
            )
            saved += 1
        messages.success(request, f'Посещаемость сохранена для {saved} учеников.')
        return redirect('mentor_dashboard')

    # Build rows for template
    rows = []
    for enrollment in enrollments:
        s = enrollment.student
        rows.append({
            'student': s,
            'attendance': existing.get(s.id),
        })

    return render(request, 'mentor/attendance.html', {
        'lesson': lesson,
        'rows': rows,
        'status_choices': Attendance.STATUS_CHOICES,
    })


# ── KPI views ─────────────────────────────────────────────────────────────────

@login_required
def student_kpi_view(request):
    user = request.user

    if user.role == 'student':
        try:
            student = user.student_profile
        except Exception:
            messages.error(request, 'Профиль ученика не найден.')
            return redirect('home')
        kpi, _ = StudentKPI.objects.get_or_create(student=student)
        return render(request, 'kpi/student_kpi.html', {'kpi': kpi, 'student': student})

    if user.role == 'parent':
        children = Student.objects.filter(parent=user, is_active=True)
        kpi_list = []
        for child in children:
            kpi, _ = StudentKPI.objects.get_or_create(student=child)
            kpi_list.append(kpi)
        return render(request, 'kpi/student_kpi.html', {'kpi_list': kpi_list, 'is_parent': True})

    messages.error(request, 'Доступ запрещён.')
    return redirect('dashboard')


@login_required
@user_passes_test(is_mentor)
def mentor_kpi_view(request):
    try:
        mentor = request.user.mentor_profile
    except Exception:
        messages.error(request, 'Профиль тренера не найден.')
        return redirect('home')

    mentor_kpi, _ = MentorKPI.objects.get_or_create(mentor=mentor)

    # Students enrolled in mentor's courses with their KPIs
    enrolled_students = Student.objects.filter(
        enrollments__course__mentor=mentor,
        enrollments__is_active=True
    ).distinct()

    student_kpis = []
    for student in enrolled_students:
        kpi, _ = StudentKPI.objects.get_or_create(student=student)
        student_kpis.append(kpi)

    student_kpis.sort(key=lambda k: k.total_kpi, reverse=True)

    return render(request, 'kpi/mentor_kpi.html', {
        'mentor_kpi':   mentor_kpi,
        'student_kpis': student_kpis,
        'mentor':       mentor,
    })


@login_required
@user_passes_test(is_admin)
def admin_kpi_view(request):
    all_student_kpis = StudentKPI.objects.select_related(
        'student__user'
    ).order_by('-total_kpi')

    all_mentor_kpis = MentorKPI.objects.select_related(
        'mentor__user'
    ).order_by('-total_kpi')

    # Force-recalculate on GET with ?refresh=1
    if request.GET.get('refresh') == '1':
        for kpi in all_student_kpis:
            kpi.recalculate()
        for kpi in all_mentor_kpis:
            kpi.recalculate()
        messages.success(request, 'KPI успешно пересчитаны.')
        return redirect('admin_kpi')

    return render(request, 'kpi/admin_kpi.html', {
        'student_kpis': all_student_kpis,
        'mentor_kpis':  all_mentor_kpis,
    })


# ── Homework review views ─────────────────────────────────────────────────────

@login_required
@user_passes_test(is_mentor)
def mentor_homework_submissions(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if homework.lesson.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    submissions = HomeworkSubmission.objects.filter(
        homework=homework
    ).select_related('student__user').order_by('status', '-submitted_at')

    # Students enrolled but haven't submitted
    from .models.enrollment import Enrollment as _Enr
    enrolled_ids = set(
        _Enr.objects.filter(course=homework.lesson.course, is_active=True)
                    .values_list('student_id', flat=True)
    )
    submitted_ids = {s.student_id for s in submissions}
    not_submitted_ids = enrolled_ids - submitted_ids

    pending_count = submissions.filter(status__in=['pending', 'late']).count()
    checked_count = submissions.filter(status='checked').count()

    return render(request, 'mentor/homework_submissions.html', {
        'homework':          homework,
        'submissions':       submissions,
        'not_submitted_ids': not_submitted_ids,
        'pending_count':     pending_count,
        'checked_count':     checked_count,
    })


@login_required
@user_passes_test(is_mentor)
def mentor_review_submission(request, submission_id):
    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if submission.homework.lesson.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    if request.method == 'POST':
        grade    = request.POST.get('grade', '').strip()
        feedback = request.POST.get('feedback', '').strip()

        if grade:
            try:
                grade_val = int(grade)
                if not (1 <= grade_val <= 10):
                    raise ValueError
            except ValueError:
                messages.error(request, 'Оценка должна быть от 1 до 10.')
                return redirect('mentor_review_submission', submission_id=submission_id)
            submission.grade = grade_val
        else:
            submission.grade = None

        submission.feedback   = feedback
        submission.status     = 'checked'
        submission.checked_at = timezone.now()
        submission.save()
        messages.success(request, f'Работа {submission.student.user.get_full_name()} проверена.')
        return redirect('mentor_homework_submissions', homework_id=submission.homework_id)

    return render(request, 'mentor/review_submission.html', {
        'submission':  submission,
        'grade_range': range(1, 11),
    })


# ── Test system: student views ────────────────────────────────────────────────

@login_required
def test_topic_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Access control: must be enrolled or mentor of course or admin
    user = request.user
    if user.role == 'student':
        try:
            student = user.student_profile
        except Exception:
            return redirect('home')
        if not Enrollment.objects.filter(student=student, course=course, is_active=True).exists():
            messages.error(request, 'Вы не записаны на этот курс.')
            return redirect('course_list')
    elif user.role == 'mentor':
        try:
            mentor = user.mentor_profile
        except Exception:
            return redirect('home')
        if course.mentor != mentor:
            messages.error(request, 'Это не ваш курс.')
            return redirect('mentor_dashboard')
    elif user.role not in ('admin',):
        return redirect('dashboard')

    topics = Topic.objects.filter(course=course, is_active=True).prefetch_related(
        'tests'
    ).order_by('order', 'created_at')

    # For students: attach attempt info per test
    student_attempts = {}
    if user.role == 'student':
        attempts = TestAttempt.objects.filter(
            student=student,
            test__topic__course=course
        ).order_by('-started_at')
        for att in attempts:
            if att.test_id not in student_attempts:
                student_attempts[att.test_id] = att

    return render(request, 'tests/topic_list.html', {
        'course': course,
        'topics': topics,
        'student_attempts': student_attempts,
    })


@login_required
@user_passes_test(is_student)
def test_take(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_active=True)
    try:
        student = request.user.student_profile
    except Exception:
        return redirect('home')

    # Must be enrolled in the course
    if not Enrollment.objects.filter(
        student=student, course=test.topic.course, is_active=True
    ).exists():
        messages.error(request, 'Вы не записаны на этот курс.')
        return redirect('course_list')

    # Check max attempts
    finished_count = TestAttempt.objects.filter(
        student=student, test=test, finished_at__isnull=False
    ).count()
    if test.max_attempts > 0 and finished_count >= test.max_attempts:
        messages.warning(request, f'Вы исчерпали все {test.max_attempts} попыток.')
        last = TestAttempt.objects.filter(
            student=student, test=test, finished_at__isnull=False
        ).order_by('-started_at').first()
        if last:
            return redirect('test_result', attempt_id=last.id)
        return redirect('test_topic_list', course_id=test.topic.course_id)

    # Get or create an in-progress attempt
    attempt = TestAttempt.objects.filter(
        student=student, test=test, finished_at__isnull=True
    ).first()

    if request.method == 'POST':
        if not attempt:
            messages.error(request, 'Попытка не найдена.')
            return redirect('test_take', test_id=test_id)

        questions = test.questions.prefetch_related('answers').all()
        for question in questions:
            selected_ids = request.POST.getlist(f'q_{question.id}')
            sa, _ = StudentAnswer.objects.get_or_create(
                attempt=attempt, question=question
            )
            sa.selected_answers.set(selected_ids)
            sa.evaluate()

        attempt.finish()
        messages.success(request, f'Тест завершён! Ваш результат: {attempt.score:.0f}%')
        return redirect('test_result', attempt_id=attempt.id)

    # GET — start new attempt if none in progress
    if not attempt:
        attempt_number = finished_count + 1
        attempt = TestAttempt.objects.create(
            student=student, test=test, attempt_number=attempt_number
        )

    questions = test.questions.prefetch_related('answers').all()

    # Load previously saved answers for this attempt (if resumed)
    saved_answers = {}
    for sa in StudentAnswer.objects.filter(attempt=attempt).prefetch_related('selected_answers'):
        saved_answers[sa.question_id] = list(sa.selected_answers.values_list('id', flat=True))

    # Compute deadline for JS timer
    deadline_ts = None
    if test.time_limit_minutes > 0:
        deadline = attempt.started_at + timedelta(minutes=test.time_limit_minutes)
        deadline_ts = int(deadline.timestamp() * 1000)

    return render(request, 'tests/take_test.html', {
        'test': test,
        'attempt': attempt,
        'questions': questions,
        'saved_answers': saved_answers,
        'deadline_ts': deadline_ts,
    })


@login_required
def test_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)

    user = request.user
    # Students can only see their own results; mentors and admins can see any
    if user.role == 'student':
        try:
            student = user.student_profile
        except Exception:
            return redirect('home')
        if attempt.student != student:
            messages.error(request, 'Доступ запрещён.')
            return redirect('dashboard')
    elif user.role == 'mentor':
        try:
            mentor = user.mentor_profile
        except Exception:
            return redirect('home')
        if attempt.test.topic.course.mentor != mentor:
            messages.error(request, 'Доступ запрещён.')
            return redirect('mentor_dashboard')
    elif user.role not in ('admin',):
        return redirect('dashboard')

    raw_answers = attempt.student_answers.select_related('question').prefetch_related(
        'selected_answers', 'question__answers'
    ).order_by('question__id')

    student_answers = []
    for sa in raw_answers:
        selected_ids = set(sa.selected_answers.values_list('id', flat=True))
        answers = []
        for ans in sa.question.answers.all():
            answers.append({
                'text': ans.text,
                'is_correct': ans.is_correct,
                'is_selected': ans.id in selected_ids,
            })
        student_answers.append({
            'question': sa.question,
            'is_correct': sa.is_correct,
            'points_earned': sa.points_earned,
            'answers': answers,
        })

    # Circumference = 2 * π * 50 ≈ 314.16; dash = score% of circumference
    dash_value = round(attempt.score / 100 * 314.16, 2)

    return render(request, 'tests/test_result.html', {
        'attempt': attempt,
        'student_answers': student_answers,
        'dash_value': dash_value,
    })


@login_required
@user_passes_test(is_student)
def test_my_results(request):
    try:
        student = request.user.student_profile
    except Exception:
        return redirect('home')

    attempts = TestAttempt.objects.filter(
        student=student, finished_at__isnull=False
    ).select_related('test__topic__course').order_by('-started_at')

    from django.db.models import Avg
    agg = attempts.aggregate(avg=Avg('score'))
    avg_score = round(agg['avg'], 1) if agg['avg'] else 0
    passed_count = attempts.filter(is_passed=True).count()
    total_count = attempts.count()

    return render(request, 'tests/my_results.html', {
        'attempts': attempts,
        'avg_score': avg_score,
        'passed_count': passed_count,
        'total_count': total_count,
    })


# ── Test system: mentor management views ─────────────────────────────────────

@login_required
@user_passes_test(is_mentor)
def mentor_topic_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if course.mentor != mentor:
        messages.error(request, 'Это не ваш курс.')
        return redirect('mentor_dashboard')

    topics = Topic.objects.filter(course=course).prefetch_related('tests').order_by('order', 'created_at')
    return render(request, 'mentor/topic_list.html', {'course': course, 'topics': topics})


@login_required
@user_passes_test(is_mentor)
def mentor_topic_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if course.mentor != mentor:
        messages.error(request, 'Это не ваш курс.')
        return redirect('mentor_dashboard')

    form = TopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        topic = form.save(commit=False)
        topic.course = course
        topic.save()
        messages.success(request, f'Тема «{topic.title}» создана.')
        return redirect('mentor_topic_list', course_id=course_id)

    return render(request, 'mentor/topic_form.html', {
        'form': form, 'course': course, 'action': 'Создать тему'
    })


@login_required
@user_passes_test(is_mentor)
def mentor_test_create(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if topic.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    form = TestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        test = form.save(commit=False)
        test.topic = topic
        test.save()
        messages.success(request, f'Тест «{test.title}» создан. Теперь добавьте вопросы.')
        return redirect('mentor_question_add', test_id=test.id)

    return render(request, 'mentor/test_form.html', {
        'form': form, 'topic': topic, 'action': 'Создать тест'
    })


@login_required
@user_passes_test(is_mentor)
def mentor_test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if test.topic.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    form = TestForm(request.POST or None, instance=test)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Тест обновлён.')
        return redirect('mentor_topic_list', course_id=test.topic.course_id)

    questions = test.questions.prefetch_related('answers').all()
    return render(request, 'mentor/test_edit.html', {
        'form': form, 'test': test, 'questions': questions
    })


@login_required
@user_passes_test(is_mentor)
def mentor_question_add(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if test.topic.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    q_form = QuestionForm(request.POST or None)
    a_formset = AnswerFormSet(request.POST or None)

    if request.method == 'POST' and q_form.is_valid() and a_formset.is_valid():
        question = q_form.save(commit=False)
        question.test = test
        question.save()
        a_formset.instance = question
        a_formset.save()
        if request.POST.get('add_another'):
            messages.success(request, 'Вопрос добавлен. Добавьте ещё один.')
            return redirect('mentor_question_add', test_id=test_id)
        messages.success(request, 'Вопрос добавлен.')
        return redirect('mentor_test_edit', test_id=test_id)

    return render(request, 'mentor/question_form.html', {
        'q_form': q_form, 'a_formset': a_formset, 'test': test, 'action': 'Добавить вопрос'
    })


@login_required
@user_passes_test(is_mentor)
def mentor_question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if question.test.topic.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    q_form = QuestionForm(request.POST or None, instance=question)
    a_formset = AnswerFormSet(request.POST or None, instance=question)

    if request.method == 'POST' and q_form.is_valid() and a_formset.is_valid():
        q_form.save()
        a_formset.save()
        messages.success(request, 'Вопрос обновлён.')
        return redirect('mentor_test_edit', test_id=question.test_id)

    return render(request, 'mentor/question_form.html', {
        'q_form': q_form, 'a_formset': a_formset, 'test': question.test, 'action': 'Редактировать вопрос'
    })


@login_required
@user_passes_test(is_mentor)
def mentor_test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    try:
        mentor = request.user.mentor_profile
    except Exception:
        return redirect('home')
    if test.topic.course.mentor != mentor:
        messages.error(request, 'Доступ запрещён.')
        return redirect('mentor_dashboard')

    from django.db.models import Avg
    attempts = TestAttempt.objects.filter(
        test=test, finished_at__isnull=False
    ).select_related('student__user').order_by('student__user__last_name', '-score')

    agg = attempts.aggregate(avg=Avg('score'))
    avg_score = round(agg['avg'], 1) if agg['avg'] else 0
    passed_count = attempts.filter(is_passed=True).count()

    return render(request, 'mentor/test_results.html', {
        'test': test,
        'attempts': attempts,
        'avg_score': avg_score,
        'passed_count': passed_count,
    })

@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


@login_required
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
