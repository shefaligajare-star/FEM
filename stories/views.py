from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Story, StoryLike
from notifications.models import Notification

@login_required
def story_list(request):
    story_type = request.GET.get('type')
    stories = Story.objects.filter(is_approved=True).select_related('author').prefetch_related('likes')

    if story_type in ['SUCCESS', 'FAILURE']:
        stories = stories.filter(story_type=story_type)

    user_liked_ids = StoryLike.objects.filter(user=request.user).values_list('story_id', flat=True)

    context = {
        'stories': stories,
        'selected_type': story_type,
        'user_liked_ids': list(user_liked_ids),
    }
    return render(request, 'stories/list.html', context)

@login_required
def story_detail(request, story_id):
    story = get_object_or_404(Story.objects.select_related('author').prefetch_related('likes'), id=story_id)
    has_liked = StoryLike.objects.filter(user=request.user, story=story).exists()

    context = {
        'story': story,
        'has_liked': has_liked,
    }
    return render(request, 'stories/detail.html', context)

@login_required
def story_create(request):
    if request.method == 'POST':
        story_type = request.POST.get('story_type', 'FAILURE')
        title = request.POST.get('title', '').strip()
        context_str = request.POST.get('business_context', '').strip()
        summary = request.POST.get('summary', '').strip()
        what_happened = request.POST.get('what_happened', '').strip()
        what_i_learned = request.POST.get('what_i_learned', '').strip()
        what_i_would_do_differently = request.POST.get('what_i_would_do_differently', '').strip()
        key_takeaway = request.POST.get('key_takeaway', '').strip()

        if not title or not what_happened or not what_i_learned:
            messages.error(request, "Please fill in all core story sections.")
            return render(request, 'stories/create.html')

        story = Story.objects.create(
            author=request.user,
            story_type=story_type,
            title=title,
            business_context=context_str or 'Regional Enterprise',
            summary=summary,
            what_happened=what_happened,
            what_i_learned=what_i_learned,
            what_i_would_do_differently=what_i_would_do_differently,
            key_takeaway=key_takeaway or 'Growth comes from candid reflection.',
            is_approved=True
        )

        messages.success(request, "Your story has been shared with the FEM network! Thank you for fostering candid learning.")
        return redirect('stories:story_detail', story_id=story.id)

    return render(request, 'stories/create.html')

@login_required
def story_like(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    like, created = StoryLike.objects.get_or_create(story=story, user=request.user)

    if not created:
        like.delete()
        story.likes_count = max(0, story.likes_count - 1)
        story.save(update_fields=['likes_count'])
        liked = False
    else:
        story.likes_count += 1
        story.save(update_fields=['likes_count'])
        liked = True

    return JsonResponse({'status': 'ok', 'liked': liked, 'likes_count': story.likes_count})
