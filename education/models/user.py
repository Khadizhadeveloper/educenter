from django.db import models
from django.contrib.auth.models import AbstractUser



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