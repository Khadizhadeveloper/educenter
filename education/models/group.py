from django.db import models
from .course import Course
from .mentor import Mentor
from .student import Student


class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название группы')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, related_name='groups')
    students = models.ManyToManyField(Student, blank=True, related_name='groups')
    max_students = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['course', 'name']

    def __str__(self):
        return f'{self.name} ({self.course.name})'

    def student_count(self):
        return self.students.count()