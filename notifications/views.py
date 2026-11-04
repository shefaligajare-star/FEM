from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Notification

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Mark as read
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            notifications.filter(read_status=False).update(read_status=True)
            messages.success(request, "All notifications marked as read.")
            return redirect('notifications:list')

    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.read_status = True
    notif.save(update_fields=['read_status'])

    if notif.action_url:
        return redirect(notif.action_url)
    return redirect('notifications:list')

@login_required
def unread_count_api(request):
    count = Notification.objects.filter(recipient=request.user, read_status=False).count()
    return JsonResponse({'unread_count': count})
