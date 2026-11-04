from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from .models import MentorProfile, MentorExperience, MentorCredit, AvailabilitySlot, Expertise
from matching.models import Problem, MentorMatch, MentoringRequest, MentoringSession
from accounts.models import User
from notifications.models import Notification

def mentor_required(view_func):
    """Decorator to ensure only mentors (or admins) access mentor views."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_mentor or request.user.is_admin_user):
            messages.warning(request, "This section is dedicated to Mentors. Redirected to your dashboard.")
            return redirect('dashboard_router')
        return view_func(request, *args, **kwargs)
    return _wrapped

@mentor_required
def dashboard(request):
    profile, _ = MentorProfile.objects.get_or_create(
        user=request.user,
        defaults={'professional_title': 'Strategic Business Mentor'}
    )
    credits, _ = MentorCredit.objects.get_or_create(mentor=profile)

    # Pending requests
    pending_requests = MentoringRequest.objects.filter(
        mentor=profile,
        status='PENDING'
    ).select_related('entrepreneur', 'problem').order_by('-created_at')

    # Active sessions
    upcoming_sessions = MentoringSession.objects.filter(
        request__mentor=profile,
        status='SCHEDULED'
    ).select_related('request__entrepreneur', 'request__problem').order_by('scheduled_at')

    # Problems in the ecosystem that closely match this mentor's expertise
    recommended_problems = Problem.objects.filter(
        status__in=['OPEN', 'MATCHED']
    ).exclude(entrepreneur=request.user).order_by('-created_at')[:5]

    stats = {
        'total_requests': MentoringRequest.objects.filter(mentor=profile).count(),
        'pending_requests': pending_requests.count(),
        'active_mentees': MentoringRequest.objects.filter(mentor=profile, status='ACCEPTED').values('entrepreneur').distinct().count(),
        'credit_score': credits.credit_score,
        'rating': credits.positive_feedback_rating,
    }

    context = {
        'profile': profile,
        'credits': credits,
        'pending_requests': pending_requests,
        'upcoming_sessions': upcoming_sessions,
        'recommended_problems': recommended_problems,
        'stats': stats,
    }
    return render(request, 'mentor/dashboard.html', context)

@mentor_required
def requests_list(request):
    profile = get_object_or_404(MentorProfile, user=request.user)
    requests = MentoringRequest.objects.filter(mentor=profile).select_related('entrepreneur', 'problem').order_by('-created_at')
    return render(request, 'mentor/requests.html', {'profile': profile, 'requests': requests})

@mentor_required
def respond_request(request, request_id, action):
    profile = get_object_or_404(MentorProfile, user=request.user)
    req = get_object_or_404(MentoringRequest, id=request_id, mentor=profile)

    if action == 'accept':
        req.status = 'ACCEPTED'
        req.save()

        # Provision a mentoring session automatically
        session, _ = MentoringSession.objects.get_or_create(
            request=req,
            defaults={
                'scheduled_at': timezone.now() + datetime.timedelta(days=3, hours=4),
                'duration_minutes': 45,
                'status': 'SCHEDULED',
                'meeting_link': f'https://fem.network/rooms/session-{req.id}'
            }
        )

        Notification.objects.create(
            recipient=req.entrepreneur,
            notification_type='REQUEST_ACCEPTED',
            title=f"{request.user.get_full_name()} accepted your mentoring request!",
            message=f"Session scheduled for problem: '{req.problem.title}'. View session details in your dashboard.",
            action_url='/entrepreneur/problems/'
        )

        # Update Mentor Credits
        credits = profile.credits
        credits.entrepreneurs_mentored += 1
        credits.save()

        messages.success(request, f"You accepted {req.entrepreneur.get_full_name()}'s request. Session scheduled.")
    elif action == 'decline':
        req.status = 'DECLINED'
        req.save()
        messages.info(request, "Request declined.")

    return redirect('mentor:requests')

@mentor_required
def complete_session(request, session_id):
    profile = get_object_or_404(MentorProfile, user=request.user)
    session = get_object_or_404(MentoringSession, id=session_id, request__mentor=profile)

    if request.method == 'POST':
        notes = request.POST.get('mentor_notes', '').strip()
        session.status = 'COMPLETED'
        session.mentor_notes = notes
        session.save()

        req = session.request
        req.status = 'COMPLETED'
        req.save()

        # Update Mentor Credits
        credits = profile.credits
        credits.mentoring_hours += 1
        credits.successful_outcomes += 1
        if req.problem.is_rural_business:
            credits.rural_businesses_supported += 1
        credits.save()

        Notification.objects.create(
            recipient=req.entrepreneur,
            notification_type='REQUEST_ACCEPTED',
            title="Mentoring session completed",
            message=f"{request.user.get_full_name()} recorded notes for your session on '{req.problem.title}'.",
            action_url='/entrepreneur/problems/'
        )

        messages.success(request, f"Session marked completed! Mentor Credits updated (+{credits.credit_score} pts total).")
        return redirect('mentor:dashboard')

    return render(request, 'mentor/session_complete.html', {'session': session})

@mentor_required
def mentees_list(request):
    profile = get_object_or_404(MentorProfile, user=request.user)
    accepted_requests = MentoringRequest.objects.filter(
        mentor=profile,
        status__in=['ACCEPTED', 'COMPLETED']
    ).select_related('entrepreneur__entrepreneur_profile', 'problem', 'session').order_by('-created_at')

    return render(request, 'mentor/entrepreneurs.html', {'profile': profile, 'accepted_requests': accepted_requests})

@mentor_required
def mentor_credits_view(request):
    profile = get_object_or_404(MentorProfile, user=request.user)
    credits, _ = MentorCredit.objects.get_or_create(mentor=profile)
    completed_sessions = MentoringSession.objects.filter(request__mentor=profile, status='COMPLETED').select_related('request__entrepreneur', 'request__problem')
    
    return render(request, 'mentor/mentor_credits.html', {
        'profile': profile,
        'credits': credits,
        'completed_sessions': completed_sessions
    })

@mentor_required
def availability_view(request):
    profile = get_object_or_404(MentorProfile, user=request.user)
    slots = AvailabilitySlot.objects.filter(mentor=profile).order_by('day_of_week', 'start_time')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            day = request.POST.get('day_of_week')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            stype = request.POST.get('slot_type', '1-on-1 Problem Diagnostic (45 min)')
            if day and start and end:
                AvailabilitySlot.objects.create(
                    mentor=profile,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    slot_type=stype,
                    is_active=True
                )
                messages.success(request, "Availability slot added.")
        elif action == 'delete':
            slot_id = request.POST.get('slot_id')
            AvailabilitySlot.objects.filter(id=slot_id, mentor=profile).delete()
            messages.info(request, "Availability slot removed.")

        return redirect('mentor:availability')

    return render(request, 'mentor/availability.html', {'profile': profile, 'slots': slots})

@mentor_required
def profile_view(request):
    profile = get_object_or_404(MentorProfile, user=request.user)
    all_expertises = Expertise.objects.all()

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.city = request.POST.get('city', user.city).strip()
        user.region = request.POST.get('region', user.region).strip()
        user.bio = request.POST.get('bio', user.bio).strip()
        user.save()

        profile.professional_title = request.POST.get('professional_title', profile.professional_title).strip()
        profile.biography = request.POST.get('biography', profile.biography).strip()
        profile.years_of_experience = int(request.POST.get('years_of_experience') or profile.years_of_experience)
        profile.primary_industry = request.POST.get('primary_industry', profile.primary_industry).strip()
        profile.rural_business_experience = 'rural_business_experience' in request.POST
        profile.is_accepting_mentees = 'is_accepting_mentees' in request.POST
        profile.save()

        selected_exp_ids = request.POST.getlist('expertises')
        profile.expertises.set(selected_exp_ids)

        # Experience adding
        new_ptype = request.POST.get('new_problem_type', '').strip()
        new_desc = request.POST.get('new_exp_desc', '').strip()
        new_outcome = request.POST.get('new_exp_outcome', '').strip()
        new_ind = request.POST.get('new_exp_industry', '').strip() or profile.primary_industry

        if new_ptype and new_outcome:
            MentorExperience.objects.create(
                mentor=profile,
                industry=new_ind,
                problem_type=new_ptype,
                description=new_desc or f"Guided regional founders facing {new_ptype}.",
                outcome=new_outcome,
                years_of_experience=3,
                is_rural_focused=profile.rural_business_experience
            )
            messages.success(request, "New verified experience added to your mentor profile!")

        messages.success(request, "Mentor profile updated.")
        return redirect('mentor:profile')

    return render(request, 'mentor/profile.html', {'profile': profile, 'all_expertises': all_expertises})
