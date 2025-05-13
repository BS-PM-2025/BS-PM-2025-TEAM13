from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import export_requests_excel

urlpatterns = [
    path('register/', views.Registration.as_view(), name = 'register'),
    path('login/', views.login_request, name = 'login'),
    path('home/', views.home, name = 'home'),
    path('logout/', views.logout_view, name= 'logout'),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="password_reset.html"),
          name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_sent.html"),
          name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view
         (template_name="password_reset_form.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view
         (template_name="password_reset_done.html"), name= "password_reset_complete"),
    path('profile/', views.profile_view, name='profile'),

    path('requests/export/csv/', views.export_requests_csv, name='export_requests_csv'),
    path('requests/export/excel/', views.export_requests_excel, name='export_requests_excel'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/export/excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    
    path('mark_notification_read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark_all_notifications_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('all_notifications/', views.all_notifications, name='all_notifications'),
    path('toggle_notification_status/', views.toggle_notification_status, name='toggle_notification_status'),
]
