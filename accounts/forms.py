from django import forms
from django.contrib.auth import authenticate
from .models import User

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create a secure password', 'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'class': 'form-input'}))
    role = forms.ChoiceField(
        choices=[
            ('ENTREPRENEUR', 'Entrepreneur — Looking for problem-based mentorship & collaboration'),
            ('MENTOR', 'Mentor — Experienced professional ready to advise & solve challenges')
        ],
        widget=forms.RadioSelect(attrs={'class': 'role-radio-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'city', 'region', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose username', 'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address', 'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-input'}),
            'city': forms.TextInput(attrs={'placeholder': 'City / Town', 'class': 'form-input'}),
            'region': forms.TextInput(attrs={'placeholder': 'Region / State', 'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'placeholder': 'Brief intro about your journey...', 'rows': 3, 'class': 'form-textarea'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'}))
