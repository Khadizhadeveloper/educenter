from django.db import models
from .course import Course


class Schedule(models.Model):

    WEEKDAY_CHOICES = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.course.name} - {self.get_weekday_display()} {self.start_time}"