from .models.notification import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    if request.user.role not in ('admin', 'mentor'):
        return {}
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    recent = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
    }
