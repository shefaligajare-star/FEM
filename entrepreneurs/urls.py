from django.urls import path
from . import views

app_name = 'entrepreneur'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('problems/', views.problem_list, name='problem_list'),
    path('problems/create/', views.problem_create, name='problem_create'),
    path('problems/<int:problem_id>/matches/', views.problem_matches, name='problem_matches'),
    path('mentors/<int:mentor_id>/', views.mentor_detail, name='mentor_detail'),
    path('mentors/<int:mentor_id>/request/', views.request_mentorship, name='request_mentorship'),
    path('saved/', views.saved_items, name='saved_items'),
    path('profile/', views.profile_view, name='profile'),
]
