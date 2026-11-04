from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import CommunityPost, Comment, Reaction, SavedPost
from notifications.models import Notification

@login_required
def feed_view(request):
    post_type = request.GET.get('type')
    search_q = request.GET.get('q')

    posts = CommunityPost.objects.select_related('author').prefetch_related('comments', 'reactions')

    if post_type:
        posts = posts.filter(post_type=post_type)

    if search_q:
        posts = posts.filter(
            Q(title__icontains=search_q) |
            Q(content__icontains=search_q) |
            Q(tags__icontains=search_q)
        )

    user_saved_ids = SavedPost.objects.filter(user=request.user).values_list('post_id', flat=True)
    user_reaction_ids = Reaction.objects.filter(user=request.user).values_list('post_id', flat=True)

    context = {
        'posts': posts,
        'selected_type': post_type,
        'search_q': search_q,
        'post_types': CommunityPost.POST_TYPES,
        'user_saved_ids': list(user_saved_ids),
        'user_reaction_ids': list(user_reaction_ids),
    }
    return render(request, 'community/feed.html', context)

@login_required
def post_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        post_type = request.POST.get('post_type', 'QUESTION')
        tags = request.POST.get('tags', '').strip()

        if not title or not content:
            messages.error(request, "Please enter both a title and content for your post.")
            return redirect('community:feed')

        post = CommunityPost.objects.create(
            author=request.user,
            title=title,
            content=content,
            post_type=post_type,
            tags=tags
        )

        messages.success(request, "Your post is live in the community!")
        return redirect('community:post_detail', post_id=post.id)

    return redirect('community:feed')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(CommunityPost.objects.select_related('author').prefetch_related('comments__author', 'reactions'), id=post_id)
    
    is_saved = SavedPost.objects.filter(user=request.user, post=post).exists()
    has_reacted = Reaction.objects.filter(user=request.user, post=post).exists()

    if request.method == 'POST':
        comment_content = request.POST.get('comment', '').strip()
        if comment_content:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=comment_content
            )

            # Notify author if not commenting on own post
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    notification_type='COMMENT',
                    title=f"New comment from {request.user.get_full_name() or request.user.username}",
                    message=f"Commented on '{post.title}': {comment_content[:80]}...",
                    action_url=f"/community/{post.id}/"
                )

            messages.success(request, "Comment published.")
            return redirect('community:post_detail', post_id=post.id)

    context = {
        'post': post,
        'is_saved': is_saved,
        'has_reacted': has_reacted,
    }
    return render(request, 'community/detail.html', context)

@login_required
def react_api(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    reaction, created = Reaction.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'reaction_type': 'LIKE'}
    )

    if not created:
        reaction.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save(update_fields=['likes_count'])
        reacted = False
    else:
        post.likes_count += 1
        post.save(update_fields=['likes_count'])
        reacted = True

    return JsonResponse({'status': 'ok', 'reacted': reacted, 'likes_count': post.likes_count})

@login_required
def save_toggle(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)

    if not created:
        saved.delete()
        is_saved = False
        messages.info(request, "Removed from saved posts.")
    else:
        is_saved = True
        messages.success(request, "Saved to your bookmarks.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_saved': is_saved})

    return redirect(request.META.get('HTTP_REFERER', 'community:feed'))

@login_required
def report_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    post.is_reported = True
    post.save(update_fields=['is_reported'])
    messages.info(request, "Thank you. This post has been flagged for administrator moderation.")
    return redirect('community:feed')
