from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .user import User




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