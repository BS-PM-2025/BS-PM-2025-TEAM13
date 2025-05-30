from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from .views import export_requests_excel

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_request, name='login'),
    path('get-courses/', views.get_courses, name='get_courses'),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),

    # איפוס סיסמה
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="password_reset.html"),
         name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_sent.html"),
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
         template_name="password_reset_form.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
         template_name="password_reset_done.html"), name="password_reset_complete"),

    # פרופיל והרשמה
    path('profile/', views.profile_view, name='profile'),
    path('registration-success/<int:user_id>/', views.registration_success, name='registration_success'),

    # בקשות
    path('requests/', views.list_requests, name='list_requests'),
    path('requests/create/', views.create_request, name='create_request'),
    path('requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<int:request_id>/update/', views.update_request_status, name='update_request_status'),
    path('requests/export/csv/', views.export_requests_csv, name='export_requests_csv'),
    path('requests/export/excel/', views.export_requests_excel, name='export_requests_excel'),
    path('bulk-delete-requests/', views.bulk_delete_requests, name='bulk_delete_requests'),

    # דשבורד ומחלקה
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/export/excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    
    # אישור מרצים וקורסים
    path('approve-lecturer/', views.approve_lecturer, name='approve_lecturer'),
    path('add-course/', views.add_course, name='add_course'),
    path('bulk-delete-students/', views.bulk_delete_students, name='bulk_delete_students'),
     path('bulk-deactivate-lecturers/', views.bulk_deactivate_lecturers, name='bulk_deactivate_lecturers'),
     path('bulk-delete-courses/', views.bulk_delete_courses, name='bulk_delete_courses'),

    # ניהול סטודנטים
    path('student-requests/<int:student_id>/', views.student_requests, name='student_requests'),
    path('activate-student/<int:student_id>/', views.activate_student, name='activate_student'),
    path('edit-student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('assign-student-courses/<int:student_id>/', views.assign_student_courses, name='assign_student_courses'),
    path('deactivate-student/<int:student_id>/', views.deactivate_student, name='deactivate_student'),
    path('edit-student-form/<int:student_id>/', views.edit_student_form, name='edit_student_form'),
    path('assign-student-courses-form/<int:student_id>/', views.assign_student_courses_form, name='assign_student_courses_form'),
    path('confirm-deactivate-student/<int:student_id>/', views.confirm_deactivate_student, name='confirm_deactivate_student'),

    # ניהול משתמשים (מזכירות)
    path('manage-users/', views.manage_users, name='manage_users'),

    # צ'אט עם AI
    path('chat-response/', views.website_chat_response, name='chat_response'),

     #התראות - פעמון
     path('mark_notification_read/', views.mark_notification_read, name='mark_notification_read'),
     path('mark_all_notifications_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
     path('all_notifications/', views.all_notifications, name='all_notifications'),
     path('toggle_notification_status/', views.toggle_notification_status, name='toggle_notification_status'),

    path('courses/manage/', views.manage_courses, name='manage_courses'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('assign-lecturer-courses-form/<int:course_id>/', views.assign_lecturer_courses_form, name='assign_lecturer_courses_form'),
    path('assign-students-to-course/<int:course_id>/', views.assign_students_to_course, name='assign_students_to_course'),
    path('assign-lecturers-to-course/<int:course_id>/', views.assign_lecturers_to_course, name='assign_lecturers_to_course'),

    path('rating/', views.rating_page, name='rating_page'),
    path('rating/submit/', views.submit_review, name='submit_review'),
    path('rating/edit/', views.edit_review, name='edit_review'),
    path('rating/delete/', views.delete_review, name='delete_review'),
    path('api/rating-stats/', views.get_rating_stats, name='get_rating_stats'),

]

# תמיכה בהצגת קבצים (למשל attachments)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
