from django.db import models
from django.utils import timezone
from .user import User






class Mentor(models.Model):
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