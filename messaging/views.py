import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Conversation, Message
from accounts.models import User
from notifications.models import Notification

@login_required
def inbox_view(request):
    conversations = Conversation.objects.filter(
        Q(participant_1=request.user) | Q(participant_2=request.user)
    ).select_related('participant_1', 'participant_2').prefetch_related('messages')

    active_conv_id = request.GET.get('c')
    active_conv = None

    if active_conv_id:
        active_conv = conversations.filter(id=active_conv_id).first()
    elif conversations.exists():
        active_conv = conversations.first()

    messages_list = []
    other_participant = None

    if active_conv:
        other_participant = active_conv.get_other_participant(request.user)
        # Mark incoming messages as read
        active_conv.messages.filter(read_status=False).exclude(sender=request.user).update(read_status=True)
        messages_list = active_conv.messages.all().select_related('sender')

    # Users available to message (mentors and fellow entrepreneurs)
    available_users = User.objects.exclude(id=request.user.id).order_by('first_name')[:25]

    context = {
        'conversations': conversations,
        'active_conv': active_conv,
        'messages_list': messages_list,
        'other_participant': other_participant,
        'available_users': available_users,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        return redirect('messaging:inbox')

    conv, created = Conversation.get_or_create_conversation(
        request.user, other_user,
        subject=f"Discussion between {request.user.display_name} and {other_user.display_name}"
    )

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=content,
                sync_status='SYNCED'
            )
            Notification.objects.create(
                recipient=other_user,
                notification_type='NEW_MESSAGE',
                title=f"New message from {request.user.display_name}",
                message=content[:80],
                action_url=f"/messages/?c={conv.id}"
            )

    return redirect(f"/messages/?c={conv.id}")

@login_required
def send_message_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        conv_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        recipient_id = data.get('recipient_id')
    except Exception:
        conv_id = request.POST.get('conversation_id')
        content = request.POST.get('content', '').strip()
        recipient_id = request.POST.get('recipient_id')

    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)

    if conv_id:
        conv = get_object_or_404(Conversation, id=conv_id)
    elif recipient_id:
        other_user = get_object_or_404(User, id=recipient_id)
        conv, _ = Conversation.get_or_create_conversation(request.user, other_user)
    else:
        return JsonResponse({'error': 'Conversation or recipient required'}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        content=content,
        sync_status='SYNCED'
    )

    other = conv.get_other_participant(request.user)
    Notification.objects.create(
        recipient=other,
        notification_type='NEW_MESSAGE',
        title=f"New message from {request.user.display_name}",
        message=content[:80],
        action_url=f"/messages/?c={conv.id}"
    )

    return JsonResponse({
        'status': 'ok',
        'message_id': msg.id,
        'sender': request.user.display_name,
        'content': msg.content,
        'created_at': msg.created_at.strftime('%I:%M %p'),
        'sync_status': msg.sync_status
    })
