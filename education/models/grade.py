from django.db import models
from .student import Student
from .course import Course
from .lesson import Lesson

class Grade(models.Model):

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