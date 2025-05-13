from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import export_requests_excel

urlpatterns = [
    path('register/', views.register_view, name = 'register'),
    path('login/', views.login_request, name = 'login'),
    path('get-courses/', views.get_courses, name='get_courses'),
    path('', views.home, name = 'home'),
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

    path('registration-success/<int:user_id>/', views.registration_success, name='registration_success'),
    path('requests/', views.list_requests, name='list_requests'),
    path('requests/create/', views.create_request, name='create_request'),
    path('requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<int:request_id>/update/', views.update_request_status, name='update_request_status'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/export/csv/', views.export_requests_csv, name='export_requests_csv'),
    path('requests/export/excel/', views.export_requests_excel, name='export_requests_excel'),
    path('my-department/', views.department_dashboard, name='department_dashboard'),
    path('approve-lecturer/', views.approve_lecturer, name='approve_lecturer'),
    path('add-course/', views.add_course, name='add_course'),
    path('student-requests/<int:student_id>/', views.student_requests, name='student_requests'),
    path('activate-student/<int:student_id>/', views.activate_student, name='activate_student'),
    path('edit-student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('assign-student-courses/<int:student_id>/', views.assign_student_courses, name='assign_student_courses'),
    path('deactivate-student/<int:student_id>/', views.deactivate_student, name='deactivate_student'),
    path('edit-student-form/<int:student_id>/', views.edit_student_form, name='edit_student_form'),
    path('assign-student-courses-form/<int:student_id>/', views.assign_student_courses_form, name='assign_student_courses_form'),
    path('confirm-deactivate-student/<int:student_id>/', views.confirm_deactivate_student, name='confirm_deactivate_student'),
    # path('course-requests/<int:course_id>/', views.course_requests, name='course_requests'),
    #path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    #path('assign-course-lecturers/<int:course_id>/', views.assign_course_lecturers, name='assign_course_lecturers'),
    # path('send-message/', views.send_message, name='send_message'),
    path('requests/export/csv/', views.export_requests_csv, name='export_requests_csv'),
    path('requests/export/excel/', views.export_requests_excel, name='export_requests_excel'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/export/excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    
    path('mark_notification_read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark_all_notifications_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('all_notifications/', views.all_notifications, name='all_notifications'),
    path('toggle_notification_status/', views.toggle_notification_status, name='toggle_notification_status'),
]
