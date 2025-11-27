from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Расширенная модель пользователя с ролями"""
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('mentor', 'Ментор'),
        ('parent', 'Родитель'),
        ('student', 'Ученик'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='parent')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class Student(models.Model):
    """Модель ученика"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='children',
                               limit_choices_to={'role': 'parent'})
    grade = models.CharField(max_length=10)
    enrollment_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    medical_info = models.TextField(blank=True, help_text="Медицинская информация")

    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'

    def __str__(self):
        return self.user.get_full_name()


class Mentor(models.Model):
    """Модель ментора/преподавателя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    photo = models.ImageField(upload_to='mentors/', blank=True, null=True, verbose_name='Фото ментора')
    specialization = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    education = models.TextField(blank=True)
    hire_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Ментор'
        verbose_name_plural = 'Менторы'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization}"


class Course(models.Model):
    """Модель курса"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.ImageField(upload_to='course_icons/', blank=True, null=True, verbose_name='Иконка курса')
    cover_image = models.ImageField(upload_to='course_covers/', blank=True, null=True, verbose_name='Обложка курса')
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, related_name='courses')
    duration_weeks = models.IntegerField()
    max_students = models.IntegerField(default=15)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    """Модель записи на курс"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} - {self.course}"


class Schedule(models.Model):
    """Модель расписания занятий"""
    WEEKDAY_CHOICES = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.course.name} - {self.get_weekday_display()} {self.start_time}"


class Lesson(models.Model):
    """Модель конкретного занятия"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    is_cancelled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.course.name} - {self.title} ({self.date})"


class Homework(models.Model):
    """Модель домашнего задания"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='homeworks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    file = models.FileField(upload_to='homework_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.lesson.course.name} - {self.title}"


class HomeworkSubmission(models.Model):
    """Модель сдачи домашнего задания"""
    STATUS_CHOICES = (
        ('pending', 'Ожидает проверки'),
        ('checked', 'Проверено'),
        ('late', 'Сдано с опозданием'),
    )

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions')
    content = models.TextField()
    file = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Сдача ДЗ'
        verbose_name_plural = 'Сдачи ДЗ'
        unique_together = ('homework', 'student')

    def __str__(self):
        return f"{self.student} - {self.homework.title}"


class Attendance(models.Model):
    """Модель посещаемости"""
    STATUS_CHOICES = (
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'Уважительная причина'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ('lesson', 'student')

    def __str__(self):
        return f"{self.student} - {self.lesson} ({self.get_status_display()})"


class Grade(models.Model):
    """Модель оценки"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    grade = models.IntegerField()
    comment = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.course} - {self.grade}"


class Announcement(models.Model):
    """Модель объявлений"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    target_audience = models.CharField(max_length=20, choices=(
        ('all', 'Все'),
        ('parents', 'Родители'),
        ('students', 'Ученики'),
        ('mentors', 'Менторы'),
    ), default='all')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title