from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from accounts.models import User
from entrepreneurs.models import EntrepreneurProfile
from mentors.models import MentorProfile, MentorCredit, Expertise
from matching.models import Problem, MentorMatch, MentoringRequest, MentoringSession, ProblemCategory
from community.models import CommunityPost
from stories.models import Story
from collaboration.models import CollaborationRequest
from synchronization.models import OfflineSyncRecord

def admin_required(view_func):
    """Decorator ensuring only ADMIN users or superusers access the admin console."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin_user:
            messages.error(request, "Access restricted to Platform Administrators.")
            return redirect('dashboard_router')
        return view_func(request, *args, **kwargs)
    return _wrapped

@admin_required
def overview(request):
    total_users = User.objects.count()
    entrepreneurs_count = User.objects.filter(role=User.Role.ENTREPRENEUR).count()
    mentors_count = User.objects.filter(role=User.Role.MENTOR).count()
    problems_count = Problem.objects.count()
    requests_count = MentoringRequest.objects.count()
    accepted_requests = MentoringRequest.objects.filter(status__in=['ACCEPTED', 'COMPLETED']).count()
    posts_count = CommunityPost.objects.count()
    stories_count = Story.objects.count()
    collabs_count = CollaborationRequest.objects.count()
    sync_records_count = OfflineSyncRecord.objects.count()

    match_rate = int((accepted_requests / (requests_count or 1)) * 100)

    # Top expertise areas
    top_categories = ProblemCategory.objects.annotate(prob_count=Count('problems')).order_by('-prob_count')[:5]

    # Recent sync records
    recent_syncs = OfflineSyncRecord.objects.select_related('user').order_by('-server_timestamp')[:8]

    # Reported posts
    reported_posts = CommunityPost.objects.filter(is_reported=True).select_related('author')[:5]

    context = {
        'total_users': total_users,
        'entrepreneurs_count': entrepreneurs_count,
        'mentors_count': mentors_count,
        'problems_count': problems_count,
        'requests_count': requests_count,
        'accepted_requests': accepted_requests,
        'match_rate': match_rate,
        'posts_count': posts_count,
        'stories_count': stories_count,
        'collabs_count': collabs_count,
        'sync_records_count': sync_records_count,
        'top_categories': top_categories,
        'recent_syncs': recent_syncs,
        'reported_posts': reported_posts,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

@admin_required
def users_list(request):
    role_filter = request.GET.get('role')
    users = User.objects.all().order_by('-date_joined')
    if role_filter:
        users = users.filter(role=role_filter)
    return render(request, 'admin_dashboard/users.html', {'users': users, 'selected_role': role_filter})

@admin_required
def mentors_manage(request):
    mentors = MentorProfile.objects.select_related('user', 'credits').prefetch_related('expertises')

    if request.method == 'POST':
        mentor_id = request.POST.get('mentor_id')
        action = request.POST.get('action')
        mentor = get_object_or_404(MentorProfile, id=mentor_id)

        if action == 'verify':
            mentor.verification_status = 'VERIFIED'
            mentor.save()
            messages.success(request, f"{mentor.user.get_full_name()} verified successfully.")
        elif action == 'reject':
            mentor.verification_status = 'REJECTED'
            mentor.save()
            messages.warning(request, f"{mentor.user.get_full_name()} verification declined.")

        return redirect('admin_dashboard:mentors')

    return render(request, 'admin_dashboard/mentors.html', {'mentors': mentors})

@admin_required
def entrepreneurs_manage(request):
    entrepreneurs = EntrepreneurProfile.objects.select_related('user').annotate(
        problem_count=Count('user__problems')
    )
    return render(request, 'admin_dashboard/entrepreneurs.html', {'entrepreneurs': entrepreneurs})

@admin_required
def reports_moderation(request):
    reported_posts = CommunityPost.objects.filter(is_reported=True).select_related('author')

    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        action = request.POST.get('action')
        post = get_object_or_404(CommunityPost, id=post_id)

        if action == 'dismiss':
            post.is_reported = False
            post.save()
            messages.info(request, "Report dismissed. Post preserved.")
        elif action == 'delete':
            post.delete()
            messages.success(request, "Inappropriate post permanently removed.")

        return redirect('admin_dashboard:reports')

    return render(request, 'admin_dashboard/reports.html', {'reported_posts': reported_posts})

@admin_required
def analytics_view(request):
    # Aggregated analytics
    total_sessions = MentoringSession.objects.count()
    completed_sessions = MentoringSession.objects.filter(status='COMPLETED').count()
    avg_rating = MentorCredit.objects.aggregate(avg_r=Avg('positive_feedback_rating'))['avg_r'] or 4.9

    category_stats = ProblemCategory.objects.annotate(cnt=Count('problems')).order_by('-cnt')
    stage_breakdown = Problem.objects.values('business_stage').annotate(count=Count('id')).order_by('-count')

    context = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'avg_rating': round(avg_rating, 2),
        'category_stats': category_stats,
        'stage_breakdown': stage_breakdown,
    }
    return render(request, 'admin_dashboard/analytics.html', context)

@admin_required
def sync_stats_view(request):
    sync_records = OfflineSyncRecord.objects.select_related('user').order_by('-server_timestamp')[:50]
    total_synced = OfflineSyncRecord.objects.filter(status='SYNCED').count()
    total_failed = OfflineSyncRecord.objects.filter(status='FAILED').count()
    total_conflicts = OfflineSyncRecord.objects.filter(status='CONFLICT').count()

    context = {
        'sync_records': sync_records,
        'total_synced': total_synced,
        'total_failed': total_failed,
        'total_conflicts': total_conflicts,
    }
    return render(request, 'admin_dashboard/sync_stats.html', context)
