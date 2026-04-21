from django.db import models
from .lesson import Lesson
from .student import Student
class Homework(models.Model):

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