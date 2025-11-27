from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, time

from education.models import (
    Student, Mentor, Course, Lesson, Homework, Enrollment,
    Schedule, Announcement
)

User = get_user_model()

print("Создание тестовых данных...")

# ============================
# 1) Админ (автор объявлений)
# ============================

admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    raise Exception("Нет суперюзера! Создайте его: python manage.py createsuperuser")

# ============================
# 2) Родители
# ============================

parent_names = [
    ("Айдана", "Токтобекова"),
    ("Марина", "Семенова"),
    ("Бакыт", "Асанов"),
    ("Гульнур", "Иманова"),
    ("Елена", "Орлова"),
]

parents = []

for first, last in parent_names:
    username = f"{first.lower()}_{last.lower()}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first,
            "last_name": last,
            "role": "parent",
            "email": f"{username}@gmail.com",
        }
    )
    parents.append(user)

print("Созданы родители:", len(parents))

# ============================
# 3) Ученики
# ============================

student_names = [
    ("Алина", "Курманова"),
    ("Михаил", "Сергеев"),
    ("Эмир", "Абдыкадыров"),
    ("София", "Касымова"),
    ("Артем", "Лунев"),
]

students = []

for i, (first, last) in enumerate(student_names):
    username = f"{first.lower()}_{last.lower()}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first,
            "last_name": last,
            "role": "student",
            "email": f"{username}@gmail.com",
        }
    )
    student, created = Student.objects.get_or_create(
        user=user,
        defaults={
            "parent": parents[i],
            "grade": f"{i+5}A",
            "medical_info": "Без противопоказаний",
        }
    )
    students.append(student)

print("Созданы ученики:", len(students))

# ============================
# 4) Менторы
# ============================

mentor_names = [
    ("Даниил", "Соколов", "Математика"),
    ("Айдар", "Исманов", "Физика"),
    ("Камиля", "Садыкова", "Информатика"),
    ("Руслан", "Омаров", "Английский"),
    ("Нурия", "Муратова", "Робототехника"),
]

mentors = []

for first, last, spec in mentor_names:
    username = f"{first.lower()}_{last.lower()}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first,
            "last_name": last,
            "role": "mentor",
            "email": f"{username}@gmail.com",
        }
    )
    mentor, created = Mentor.objects.get_or_create(
        user=user,
        defaults={
            "specialization": spec,
            "experience_years": 3,
            "education": "Высшее педагогическое образование",
        }
    )
    mentors.append(mentor)

print("Созданы менторы:", len(mentors))

# ============================
# 5) Курсы
# ============================

courses_info = [
    ("Математика PRO", "Углубленный курс по олимпиадной математике"),
    ("Физика START", "Основы физики для школьников"),
    ("Python Junior", "Программирование на Python с нуля"),
    ("Английский A2", "Базовая грамматика и разговорная практика"),
    ("Робототехника LEGO", "Сборка и программирование роботов"),
]

courses = []

for i, (name, desc) in enumerate(courses_info):
    course, created = Course.objects.get_or_create(
        name=name,
        defaults={
            "description": desc,
            "mentor": mentors[i],
            "duration_weeks": 12,
            "start_date": date.today(),
            "end_date": date.today() + timedelta(weeks=12),
        }
    )
    courses.append(course)

print("Созданы курсы:", len(courses))

# ============================
# 6) Записи на курсы
# ============================

for i in range(5):
    Enrollment.objects.get_or_create(
        student=students[i],
        course=courses[i],
    )

print("Созданы записи на курсы: 5")

# ============================
# 7) Расписание
# ============================

for i, course in enumerate(courses):
    Schedule.objects.get_or_create(
        course=course,
        weekday=i,
        start_time=time(15, 0),
        end_time=time(16, 30),
        room=f"Кабинет {101+i}",
    )

print("Создано расписание: 5")

# ============================
# 8) Занятия
# ============================

lessons = []

for i, course in enumerate(courses):
    lesson, created = Lesson.objects.get_or_create(
        course=course,
        title=f"Урок #{i+1}",
        defaults={
            "description": "Тема занятия — введение и базовая теория.",
            "date": date.today() + timedelta(days=i),
            "start_time": time(15, 0),
            "end_time": time(16, 30),
            "room": f"Кабинет {101+i}",
        }
    )
    lessons.append(lesson)

print("Созданы занятия: 5")

# ============================
# 9) Домашние задания
# ============================

for i, lesson in enumerate(lessons):
    Homework.objects.get_or_create(
        lesson=lesson,
        title=f"Домашнее задание №{i+1}",
        defaults={
            "description": "Выполнить упражнения из учебника.",
            "due_date": timezone.now() + timedelta(days=3),
        }
    )

print("Создано ДЗ: 5")

# ============================
# 10) Объявления
# ============================

announcements_data = [
    ("Добро пожаловать!", "Старт зимнего учебного модуля!", "all"),
    ("Собрание родителей", "Собрание в субботу в 11:00", "parents"),
    ("Олимпиада", "Регистрация на олимпиаду по математике", "students"),
    ("Планерка", "Планерка для менторов в пятницу", "mentors"),
    ("Замена занятия", "Завтрашний урок переносится на понедельник", "all"),
]

for title, content, audience in announcements_data:
    Announcement.objects.get_or_create(
        title=title,
        defaults={
            "content":content,
            "author": admin_user,
            "target_audience": audience,
            "is_pinned": False
        }
    )

print("Созданы объявления: 5")

print("\n==============================")
print("  ТЕСТОВЫЕ ДАННЫЕ СОЗДАНЫ 🎉")
print("==============================")
