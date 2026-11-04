from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from accounts.models import User
from .models import EntrepreneurProfile
from mentors.models import MentorProfile, MentorExperience, MentorCredit, Expertise
from matching.models import Problem, ProblemCategory, MentorMatch, MentoringRequest, MentoringSession
from matching.engine import run_matching_engine_for_problem
from community.models import CommunityPost, SavedPost
from collaboration.models import CollaborationRequest, CollaborationInterest
from stories.models import Story
from notifications.models import Notification

def entrepreneur_required(view_func):
    """Decorator to ensure only entrepreneurs (or admins) access entrepreneur views."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_entrepreneur or request.user.is_admin_user):
            messages.warning(request, "This section is dedicated to Entrepreneurs. Redirected to your dashboard.")
            return redirect('dashboard_router')
        return view_func(request, *args, **kwargs)
    return _wrapped

@entrepreneur_required
def dashboard(request):
    user = request.user
    profile, _ = EntrepreneurProfile.objects.get_or_create(user=user)

    # Active problems
    active_problems = Problem.objects.filter(entrepreneur=user).prefetch_related('matches__mentor__user')[:5]

    # Top recommended mentors based on the latest problem or platform top mentors
    top_matches = []
    latest_problem = active_problems.first()
    if latest_problem:
        top_matches = latest_problem.matches.select_related('mentor__user', 'mentor__credits').prefetch_related('mentor__expertises')[:4]
    
    if not top_matches:
        # Fallback to verified mentors with highest credits
        top_mentors = MentorProfile.objects.filter(is_accepting_mentees=True).select_related('user', 'credits').prefetch_related('expertises')[:4]
    else:
        top_mentors = None

    # Scheduled sessions
    upcoming_sessions = MentoringSession.objects.filter(
        request__entrepreneur=user,
        status='SCHEDULED'
    ).select_related('request__mentor__user').order_by('scheduled_at')[:3]

    # Recent notifications
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:4]

    # Analytics for Entrepreneur
    stats = {
        'problems_submitted': Problem.objects.filter(entrepreneur=user).count(),
        'mentors_connected': MentoringRequest.objects.filter(entrepreneur=user, status='ACCEPTED').count(),
        'active_requests': MentoringRequest.objects.filter(entrepreneur=user, status='PENDING').count(),
        'collaborations': CollaborationRequest.objects.filter(entrepreneur=user).count(),
        'community_contributions': CommunityPost.objects.filter(author=user).count() + Story.objects.filter(author=user).count()
    }

    context = {
        'profile': profile,
        'active_problems': active_problems,
        'latest_problem': latest_problem,
        'top_matches': top_matches,
        'top_mentors': top_mentors,
        'upcoming_sessions': upcoming_sessions,
        'notifications': notifications,
        'stats': stats,
    }
    return render(request, 'entrepreneur/dashboard.html', context)

@entrepreneur_required
def problem_list(request):
    problems = Problem.objects.filter(entrepreneur=request.user).prefetch_related('matches', 'requests')
    return render(request, 'entrepreneur/problems.html', {'problems': problems})

@entrepreneur_required
def problem_create(request):
    categories = ProblemCategory.objects.all()
    profile = getattr(request.user, 'entrepreneur_profile', None)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        industry = request.POST.get('industry', '').strip() or (profile.industry if profile else 'Agri-Business')
        business_stage = request.POST.get('business_stage', '').strip() or 'Early Stage'
        urgency = request.POST.get('urgency', 'HIGH')
        desired_support = request.POST.get('desired_support', '').strip() or '1-on-1 Mentorship & Diagnostic'
        is_rural = 'is_rural_business' in request.POST
        location = request.POST.get('location', '').strip() or (request.user.city or 'Regional')

        if not title or not description:
            messages.error(request, "Please provide a clear title and description for your business challenge.")
            return render(request, 'entrepreneur/problem_create.html', {'categories': categories, 'profile': profile})

        cat_obj = ProblemCategory.objects.filter(id=category_id).first() if category_id else None

        problem = Problem.objects.create(
            entrepreneur=request.user,
            title=title,
            description=description,
            category=cat_obj,
            industry=industry,
            business_stage=business_stage,
            urgency=urgency,
            desired_support=desired_support,
            is_rural_business=is_rural,
            location=location,
            status='OPEN'
        )

        # Run intelligent matching engine immediately
        matches = run_matching_engine_for_problem(problem)

        Notification.objects.create(
            recipient=request.user,
            notification_type='RECOMMENDATION',
            title=f"Matches ready for '{problem.title}'",
            message=f"FEM evaluated your problem against all mentor profiles and identified {len(matches)} suitable mentors.",
            action_url=f"/entrepreneur/problems/{problem.id}/matches/"
        )

        messages.success(request, f"Problem submitted! We found {len(matches)} mentors who have solved similar challenges.")
        return redirect('entrepreneur:problem_matches', problem_id=problem.id)

    return render(request, 'entrepreneur/problem_create.html', {'categories': categories, 'profile': profile})

@entrepreneur_required
def problem_matches(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, entrepreneur=request.user)
    matches = problem.matches.select_related('mentor__user', 'mentor__credits').prefetch_related('mentor__expertises', 'mentor__experiences')

    if not matches.exists():
        matches = run_matching_engine_for_problem(problem)

    # Check which mentors have already been requested
    requested_mentor_ids = MentoringRequest.objects.filter(
        problem=problem,
        entrepreneur=request.user
    ).values_list('mentor_id', flat=True)

    context = {
        'problem': problem,
        'matches': matches,
        'requested_mentor_ids': list(requested_mentor_ids),
    }
@entrepreneur_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, entrepreneur=request.user)
    categories = ProblemCategory.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'close':
            problem.status = 'RESOLVED'
            problem.save()
            messages.success(request, f"Problem '{problem.title}' marked as resolved.")
            return redirect('entrepreneur:problem_detail', problem_id=problem.id)
        elif action == 'reopen':
            problem.status = 'OPEN'
            problem.save()
            messages.success(request, f"Problem '{problem.title}' reopened.")
            return redirect('entrepreneur:problem_detail', problem_id=problem.id)
        elif action == 'edit':
            problem.title = request.POST.get('title', problem.title).strip()
            problem.description = request.POST.get('description', problem.description).strip()
            cat_id = request.POST.get('category')
            if cat_id:
                problem.category = ProblemCategory.objects.filter(id=cat_id).first()
            problem.industry = request.POST.get('industry', problem.industry).strip()
            problem.urgency = request.POST.get('urgency', problem.urgency)
            problem.save()
            run_matching_engine_for_problem(problem)
            messages.success(request, "Problem updated and mentor matches refreshed.")
            return redirect('entrepreneur:problem_detail', problem_id=problem.id)

    matches = problem.matches.select_related('mentor__user', 'mentor__credits')[:5]
    requests = problem.requests.select_related('mentor__user')

    context = {
        'problem': problem,
        'categories': categories,
        'matches': matches,
        'requests': requests,
    }
    return render(request, 'entrepreneur/problem_detail.html', context)

@entrepreneur_required
def mentor_detail(request, mentor_id):
    mentor = get_object_or_404(MentorProfile.objects.select_related('user', 'credits').prefetch_related('expertises', 'experiences', 'availability_slots'), id=mentor_id)
    
    # Check if entrepreneur has any problems to connect with
    user_problems = Problem.objects.filter(entrepreneur=request.user).order_by('-created_at')
    
    # Check if there is an existing match score for this mentor and latest problem
    match_record = None
    if user_problems.exists():
        match_record = MentorMatch.objects.filter(problem=user_problems.first(), mentor=mentor).first()

    # Existing requests
    existing_request = MentoringRequest.objects.filter(entrepreneur=request.user, mentor=mentor).first()

    context = {
        'mentor': mentor,
        'user_problems': user_problems,
        'match_record': match_record,
        'existing_request': existing_request,
    }
    return render(request, 'entrepreneur/mentor_detail.html', context)

@entrepreneur_required
def request_mentorship(request, mentor_id):
    if request.method != 'POST':
        return redirect('entrepreneur:mentor_detail', mentor_id=mentor_id)

    mentor = get_object_or_404(MentorProfile, id=mentor_id)
    problem_id = request.POST.get('problem_id')
    message_text = request.POST.get('message', '').strip()

    problem = get_object_or_404(Problem, id=problem_id, entrepreneur=request.user)

    if not message_text:
        messages.error(request, "Please include a personal note explaining why you'd value this mentor's guidance.")
        return redirect('entrepreneur:mentor_detail', mentor_id=mentor_id)

    req, created = MentoringRequest.objects.get_or_create(
        problem=problem,
        entrepreneur=request.user,
        mentor=mentor,
        defaults={'message': message_text, 'status': 'PENDING'}
    )

    if not created:
        req.message = message_text
        req.status = 'PENDING'
        req.save()

    # Notify mentor
    Notification.objects.create(
        recipient=mentor.user,
        notification_type='MENTOR_REQUEST',
        title=f"New mentorship request from {request.user.get_full_name() or request.user.username}",
        message=f"Problem: '{problem.title}' — {message_text[:120]}...",
        action_url='/mentor/requests/'
    )

    messages.success(request, f"Mentorship request sent to {mentor.user.get_full_name()}! You'll be notified when they review it.")
    return redirect('entrepreneur:problem_matches', problem_id=problem.id)

@entrepreneur_required
def saved_items(request):
    saved_posts = SavedPost.objects.filter(user=request.user).select_related('post__author')
    return render(request, 'entrepreneur/saved_items.html', {'saved_posts': saved_posts})

@entrepreneur_required
def profile_view(request):
    profile, _ = EntrepreneurProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.city = request.POST.get('city', user.city).strip()
        user.region = request.POST.get('region', user.region).strip()
        user.bio = request.POST.get('bio', user.bio).strip()
        user.save()

        profile.business_name = request.POST.get('business_name', profile.business_name).strip()
        profile.industry = request.POST.get('industry', profile.industry).strip()
        profile.business_stage = request.POST.get('business_stage', profile.business_stage).strip()
        profile.location = request.POST.get('location', profile.location).strip()
        profile.is_rural_business = 'is_rural_business' in request.POST
        profile.description = request.POST.get('description', profile.description).strip()
        profile.skills = request.POST.get('skills', profile.skills).strip()
        profile.collaboration_interests = request.POST.get('collaboration_interests', profile.collaboration_interests).strip()
        profile.save()

        messages.success(request, "Entrepreneur profile updated successfully.")
        return redirect('entrepreneur:profile')

    return render(request, 'entrepreneur/profile.html', {'profile': profile})
