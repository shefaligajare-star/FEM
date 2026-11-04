from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import CollaborationRequest, CollaborationInterest
from notifications.models import Notification

@login_required
def board_view(request):
    collab_type = request.GET.get('type')
    industry = request.GET.get('industry')
    search_q = request.GET.get('q')

    requests = CollaborationRequest.objects.filter(status='OPEN').select_related('entrepreneur')

    if collab_type:
        requests = requests.filter(collaboration_type=collab_type)
    if industry:
        requests = requests.filter(industry__icontains=industry)
    if search_q:
        requests = requests.filter(
            Q(title__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(tags__icontains=search_q) |
            Q(location__icontains=search_q)
        )

    my_proposals = CollaborationInterest.objects.filter(entrepreneur=request.user).values_list('collaboration_id', flat=True)

    context = {
        'requests': requests,
        'selected_type': collab_type,
        'search_q': search_q,
        'collab_types': CollaborationRequest.COLLAB_TYPES,
        'my_proposals': list(my_proposals),
    }
    return render(request, 'collaboration/board.html', context)

@login_required
def create_request(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        industry = request.POST.get('industry', 'Food & Agriculture').strip()
        collaboration_type = request.POST.get('collaboration_type', 'SUPPLY_CHAIN')
        location = request.POST.get('location', 'Regional').strip()
        tags = request.POST.get('tags', '').strip()

        if not title or not description:
            messages.error(request, "Please fill in title and description.")
            return redirect('collaboration:board')

        collab = CollaborationRequest.objects.create(
            entrepreneur=request.user,
            title=title,
            description=description,
            industry=industry,
            collaboration_type=collaboration_type,
            location=location,
            tags=tags,
            status='OPEN'
        )

        messages.success(request, "Your collaboration opportunity is published to the network!")
        return redirect('collaboration:board')

    return render(request, 'collaboration/create.html', {'collab_types': CollaborationRequest.COLLAB_TYPES})

@login_required
def express_interest(request, collab_id):
    collab = get_object_or_404(CollaborationRequest, id=collab_id)

    if collab.entrepreneur == request.user:
        messages.warning(request, "You cannot express interest in your own collaboration request.")
        return redirect('collaboration:board')

    if request.method == 'POST':
        pitch = request.POST.get('pitch', '').strip()
        if not pitch:
            messages.error(request, "Please share a brief pitch on how you can collaborate.")
            return redirect('collaboration:board')

        interest, created = CollaborationInterest.objects.get_or_create(
            collaboration=collab,
            entrepreneur=request.user,
            defaults={'pitch_message': pitch, 'status': 'PENDING'}
        )

        if not created:
            interest.pitch_message = pitch
            interest.save()

        Notification.objects.create(
            recipient=collab.entrepreneur,
            notification_type='COLLABORATION_REQUEST',
            title=f"Collaboration interest from {request.user.get_full_name() or request.user.username}",
            message=f"Regarding '{collab.title}': {pitch[:100]}...",
            action_url='/entrepreneur/collaborate/'
        )

        messages.success(request, f"Interest sent to {collab.entrepreneur.get_full_name()}! You can also message them directly.")
        return redirect('collaboration:board')

    return redirect('collaboration:board')
