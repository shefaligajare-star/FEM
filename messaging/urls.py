from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('api/send/', views.send_message_api, name='send_api'),
]
