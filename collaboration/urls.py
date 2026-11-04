from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    path('', views.board_view, name='board'),
    path('create/', views.create_request, name='create'),
    path('<int:collab_id>/interest/', views.express_interest, name='express_interest'),
]
