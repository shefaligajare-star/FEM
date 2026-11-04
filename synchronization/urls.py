from django.urls import path
from . import views

app_name = 'synchronization'

urlpatterns = [
    path('api/batch/', views.sync_batch_api, name='sync_batch_api'),
    path('api/status/', views.sync_status_view, name='sync_status_view'),
]
