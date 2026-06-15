from django.db import models
from .user import User


class Notification(models.Model):
    TYPE_CHOICES = (
        ('group_full',    'Группа заполнена'),
        ('group_created', 'Новая группа создана'),
        ('general',       'Общее'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient} — {self.message[:50]}'
