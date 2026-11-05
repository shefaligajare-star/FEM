from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from accounts import views as account_views
from synchronization import views as sync_views

urlpatterns = [
    # Platform Core & Landing
    path("database-diagnostic/", views.database_diagnostic, name="database_diagnostic"),
    path('', views.landing_page, name='landing'),
    path('about/', views.about_page, name='about'),
    path('how-it-works/', views.how_it_works_page, name='how_it_works'),
    path('mentors/', views.mentor_directory_page, name='mentor_directory'),
    path('faq/', views.faq_page, name='faq'),
    path('contact/', views.contact_page, name='contact'),
    path('privacy/', views.privacy_page, name='privacy'),
    path('terms/', views.terms_page, name='terms'),
    path('search/', views.global_search, name='global_search'),

    # Authentication & Role Navigation
    path('login/', account_views.login_view, name='login'),
    path('signup/', account_views.signup_view, name='signup'),
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard_router, name='dashboard_router'),
    path('accounts/', include('accounts.urls')),

    # Role-Specific Dashboards & Workspaces
    path('entrepreneur/', include('entrepreneurs.urls', namespace='entrepreneur')),
    path('mentor/', include('mentors.urls', namespace='mentor')),
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),

    # Network Collaboration & Community
    path('community/', include('community.urls', namespace='community')),
    path('collaborate/', include('collaboration.urls', namespace='collaboration')),
    path('stories/', include('stories.urls', namespace='stories')),
    path('messages/', include('messaging.urls', namespace='messaging')),
    path('notifications/', include('notifications.urls', namespace='notifications')),

    # Offline-First Synchronization API
    path('sync/', include('synchronization.urls', namespace='synchronization')),
    path('api/sync/batch/', sync_views.sync_batch_api, name='api_sync_batch'),
    path('api/sync/status/', sync_views.sync_status_view, name='api_sync_status'),

    # Django Administration (built-in)
    path('django-admin/', admin.site.urls),
]

handler403 = 'fem.views.custom_403_view'
handler404 = 'fem.views.custom_404_view'
handler500 = 'fem.views.custom_500_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

