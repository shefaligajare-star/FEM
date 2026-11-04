from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import SignUpForm, LoginForm
from entrepreneurs.models import EntrepreneurProfile
from mentors.models import MentorProfile, MentorCredit

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_router')

    initial_role = request.GET.get('role', 'ENTREPRENEUR').upper()
    if initial_role not in ['ENTREPRENEUR', 'MENTOR']:
        initial_role = 'ENTREPRENEUR'

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            if user.role == User.Role.ENTREPRENEUR:
                EntrepreneurProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'business_name': f"{user.first_name}'s Venture" if user.first_name else "Emerging Enterprise",
                        'location': f"{user.city}, {user.region}".strip(', '),
                        'description': user.bio or 'Building an innovative business.',
                        'industry': 'Agri-Business & Food',
                        'business_stage': 'Early Stage / Prototype'
                    }
                )
            elif user.role == User.Role.MENTOR:
                profile, _ = MentorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'professional_title': 'Independent Business Advisor & Mentor',
                        'biography': user.bio or 'Passionate about guiding high-impact entrepreneurs.',
                        'years_of_experience': 5,
                        'rural_business_experience': True,
                        'primary_industry': 'General Business & Finance'
                    }
                )
                MentorCredit.objects.get_or_create(mentor=profile)

            login(request, user)
            messages.success(request, f"Welcome to FEM, {user.first_name or user.username}! Your account is active.")
            return redirect('dashboard_router')
    else:
        form = SignUpForm(initial={'role': initial_role})

    return render(request, 'registration/signup.html', {'form': form, 'initial_role': initial_role})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_router')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Try by username
            user = authenticate(request, username=username_or_email, password=password)
            if not user:
                # Try by email
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard_router')
            else:
                messages.error(request, "Invalid username or password. Please verify your credentials.")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been securely logged out.")
    return redirect('landing')

@login_required
def dashboard_router(request):
    if request.user.role == User.Role.ADMIN or request.user.is_superuser:
        return redirect('admin_dashboard:overview')
    elif request.user.role == User.Role.MENTOR:
        return redirect('mentor:dashboard')
    else:
        return redirect('entrepreneur:dashboard')

@login_required
def user_profile_view(request):
    return render(request, 'accounts/profile.html', {'user_obj': request.user})

@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.phone = request.POST.get('phone', user.phone).strip()
        user.city = request.POST.get('city', user.city).strip()
        user.region = request.POST.get('region', user.region).strip()
        user.bio = request.POST.get('bio', user.bio).strip()
        user.avatar_url = request.POST.get('avatar_url', user.avatar_url).strip()
        user.save()
        messages.success(request, "Your profile information has been successfully updated.")
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'user_obj': user})

@login_required
def change_password_view(request):
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:settings')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})

@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html', {'user_obj': request.user})

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        confirm = request.POST.get('confirm_delete')
        if confirm == 'DELETE':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your FEM account has been permanently removed.")
            return redirect('landing')
        else:
            messages.error(request, "Please type 'DELETE' to confirm account closure.")
    return render(request, 'accounts/delete_account.html')

