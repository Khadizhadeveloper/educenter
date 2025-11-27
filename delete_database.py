from education.models import *
from django.contrib.auth import get_user_model

User = get_user_model()

print("Удаление данных...")

# Удаляем в правильном порядке
Grade.objects.all().delete()
Homework.objects.all().delete()
Lesson.objects.all().delete()
Schedule.objects.all().delete()
Enrollment.objects.all().delete()
Course.objects.all().delete()
Student.objects.all().delete()
Mentor.objects.all().delete()
Announcement.objects.all().delete()

# Удаляем тестовых пользователей
User.objects.filter(username__startswith='mentor').delete()
User.objects.filter(username__startswith='parent').delete()
User.objects.filter(username__startswith='student').delete()

print("Готово! Данные удалены.")
