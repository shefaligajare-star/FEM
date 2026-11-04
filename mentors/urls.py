from django.urls import path
from . import views

app_name = 'mentor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('requests/', views.requests_list, name='requests'),
    path('requests/<int:request_id>/<str:action>/', views.respond_request, name='respond_request'),
    path('sessions/<int:session_id>/complete/', views.complete_session, name='complete_session'),
    path('entrepreneurs/', views.mentees_list, name='entrepreneurs'),
    path('credits/', views.mentor_credits_view, name='credits'),
    path('availability/', views.availability_view, name='availability'),
    path('profile/', views.profile_view, name='profile'),
]
