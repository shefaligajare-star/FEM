from django.http import HttpResponse
from django.db import connection
import os 
from django.shortcuts import render, redirect
from django.db.models import Q
from mentors.models import MentorProfile
from entrepreneurs.models import EntrepreneurProfile
from community.models import CommunityPost
from stories.models import Story
from collaboration.models import CollaborationRequest
from matching.models import Problem

def landing_page(request):
    if request.user.is_authenticated:
        # If logged in, still let them view landing, or provide link to dashboard
        pass

    featured_mentors = MentorProfile.objects.filter(is_accepting_mentees=True).select_related('user', 'credits').prefetch_related('expertises')[:3]
    featured_stories = Story.objects.filter(is_approved=True).select_related('author')[:3]
    recent_collabs = CollaborationRequest.objects.filter(status='OPEN').select_related('entrepreneur')[:3]

    context = {
        'featured_mentors': featured_mentors,
        'featured_stories': featured_stories,
        'recent_collabs': recent_collabs,
    }
    return render(request, 'landing.html', context)


# def landing_page(request):
#     return HttpResponse("Homepage is working.")

def global_search(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('cat', 'all')

    mentors = []
    entrepreneurs = []
    posts = []
    stories = []
    collabs = []

    if q:
        if category in ['all', 'mentors']:
            mentors = MentorProfile.objects.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(professional_title__icontains=q) |
                Q(biography__icontains=q) |
                Q(primary_industry__icontains=q) |
                Q(expertises__name__icontains=q)
            ).distinct().select_related('user', 'credits')[:6]

        if category in ['all', 'entrepreneurs']:
            entrepreneurs = EntrepreneurProfile.objects.filter(
                Q(business_name__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(industry__icontains=q) |
                Q(description__icontains=q)
            ).select_related('user')[:6]

        if category in ['all', 'posts']:
            posts = CommunityPost.objects.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q) |
                Q(tags__icontains=q)
            ).select_related('author')[:6]

        if category in ['all', 'stories']:
            stories = Story.objects.filter(
                Q(title__icontains=q) |
                Q(what_happened__icontains=q) |
                Q(what_i_learned__icontains=q) |
                Q(key_takeaway__icontains=q)
            ).select_related('author')[:6]

        if category in ['all', 'collabs']:
            collabs = CollaborationRequest.objects.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__icontains=q)
            ).select_related('entrepreneur')[:6]

    total_results = len(mentors) + len(entrepreneurs) + len(posts) + len(stories) + len(collabs)

    context = {
        'query': q,
        'category': category,
        'mentors': mentors,
        'entrepreneurs': entrepreneurs,
        'posts': posts,
        'stories': stories,
        'collabs': collabs,
        'total_results': total_results,
    }
    return render(request, 'search_results.html', context)

def about_page(request):
    return render(request, 'about.html')

def how_it_works_page(request):
    return render(request, 'how_it_works.html')

def mentor_directory_page(request):
    from mentors.models import Expertise
    q = request.GET.get('q', '').strip()
    expertise_filter = request.GET.get('expertise', '').strip()
    industry_filter = request.GET.get('industry', '').strip()

    mentors = MentorProfile.objects.filter(
        verification_status='VERIFIED',
        is_accepting_mentees=True
    ).select_related('user', 'credits').prefetch_related('expertises', 'experiences')

    if q:
        mentors = mentors.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(professional_title__icontains=q) |
            Q(biography__icontains=q) |
            Q(primary_industry__icontains=q)
        ).distinct()

    if expertise_filter:
        mentors = mentors.filter(expertises__slug=expertise_filter).distinct()

    if industry_filter:
        mentors = mentors.filter(primary_industry__icontains=industry_filter)

    expertises = Expertise.objects.all()

    context = {
        'mentors': mentors,
        'expertises': expertises,
        'query': q,
        'selected_expertise': expertise_filter,
        'selected_industry': industry_filter,
    }
    return render(request, 'mentor_directory.html', context)

def faq_page(request):
    return render(request, 'faq.html')

def contact_page(request):
    if request.method == 'POST':
        from django.contrib import messages
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            messages.success(request, f"Thank you, {name}! Your message has been received. Our team will contact you at {email}.")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'contact.html')

def privacy_page(request):
    return render(request, 'privacy.html')

def terms_page(request):
    return render(request, 'terms.html')

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
