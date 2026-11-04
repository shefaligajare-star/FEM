from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('users/', views.users_list, name='users'),
    path('mentors/', views.mentors_manage, name='mentors'),
    path('entrepreneurs/', views.entrepreneurs_manage, name='entrepreneurs'),
    path('reports/', views.reports_moderation, name='reports'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('sync-stats/', views.sync_stats_view, name='sync_stats'),
]
