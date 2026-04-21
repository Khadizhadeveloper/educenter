from django.db import models
from .mentor import Mentor

class Course(models.Model):

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