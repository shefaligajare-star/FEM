from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('create/', views.post_create, name='post_create'),
    path('<int:post_id>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/react/', views.react_api, name='react_api'),
    path('<int:post_id>/save/', views.save_toggle, name='save_toggle'),
    path('<int:post_id>/report/', views.report_post, name='report_post'),
]
