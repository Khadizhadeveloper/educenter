from django.db import models
from .course import Course
from .user import User


class Announcement(models.Model):

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