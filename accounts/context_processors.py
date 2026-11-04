def fem_global_context(request):
    """
    Global context processor providing branding and user notification/message counts.
    """
    context = {
        'brand_name': 'FEM',
        'app_full_name': 'Flourishing Entrepreneurs and Mentors',
        'unread_notifications_count': 0,
        'unread_messages_count': 0,
        'user_role': 'ANONYMOUS',
    }

    if request.user.is_authenticated:
        context['user_role'] = getattr(request.user, 'role', 'ENTREPRENEUR')
        try:
            from notifications.models import Notification
            context['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user, read_status=False
            ).count()
        except Exception:
            pass

        try:
            from messaging.models import Conversation, Message
            from django.db.models import Q
            user_convs = Conversation.objects.filter(
                Q(participant_1=request.user) | Q(participant_2=request.user)
            )
            context['unread_messages_count'] = Message.objects.filter(
                conversation__in=user_convs,
                read_status=False
            ).exclude(sender=request.user).count()
        except Exception:
            pass

    return context
