from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:notification_id>/read/', views.mark_read, name='mark_read'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
]
