from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from Website.models import Notification
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)


def send_request_notification(request_obj, notification_type, recipient=None):
    logger.debug(f"▶️ שליחת התראה מסוג '{notification_type}' לבקשה #{request_obj.id}")

    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
    request_url = f"{base_url}{reverse('request_detail', args=[request_obj.id])}"

    context = {
        'request': request_obj,
        'request_url': request_url,
        'notification_type': notification_type,
    }

    if recipient is None:
        if notification_type == 'created':
            recipients = [user.email for user in request_obj.assigned_to.all() if user.email]
            app_notification_recipients = list(request_obj.assigned_to.all())

        elif notification_type in ['updated', 'resolved', 'info_requested']:
            recipients = [request_obj.student.email]
            app_notification_recipients = [request_obj.student]

        elif notification_type == 'comment':
            try:
                latest_comment = request_obj.comments.latest('created')
                if latest_comment.user == request_obj.student:
                    recipients = [user.email for user in request_obj.assigned_to.all() if user.email]
                    app_notification_recipients = list(request_obj.assigned_to.all())
                else:
                    recipients = [request_obj.student.email]
                    app_notification_recipients = [request_obj.student]
            except Exception as e:
                logger.debug(f"⚠️ לא נמצאה תגובה: {e}")
                recipients = []
                app_notification_recipients = []

        else:
            recipients = []
            app_notification_recipients = []
    else:
        recipients = [recipient.email] if hasattr(recipient, 'email') else [recipient]
        app_notification_recipients = [recipient]

    if not recipients and not app_notification_recipients:
        logger.debug("🚫 אין נמענים להתראה")
        return

    subject_prefix = 'EasyREQ - '
    if notification_type == 'created':
        message = f"בקשה חדשה #{request_obj.id}: {request_obj.get_title_display()}"
        subject = f"{subject_prefix}בקשה חדשה #{request_obj.id}"
    elif notification_type == 'updated':
        message = f"סטטוס הבקשה #{request_obj.id} עודכן ל־{request_obj.get_current_status_display()}"
        subject = f"{subject_prefix}עדכון סטטוס לבקשה #{request_obj.id}"
    elif notification_type == 'comment':
        message = f"תגובה חדשה בבקשה #{request_obj.id}"
        subject = f"{subject_prefix}תגובה חדשה בבקשה"
    elif notification_type == 'resolved':
        status_text = "אושרה" if request_obj.status == 1 else "נדחתה"
        message = f"הבקשה #{request_obj.id} {status_text}"
        subject = f"{subject_prefix}בקשה {status_text}"
    elif notification_type == 'info_requested':
        message = f"נדרש מידע נוסף לבקשה #{request_obj.id}"
        subject = f"{subject_prefix}מידע נוסף נדרש"
    elif notification_type == 'assigned':
        message = f"הוקצית לטיפול בבקשה #{request_obj.id}"
        subject = f"{subject_prefix}הוקצית בקשה חדשה"
    else:
        message = f"עדכון בבקשה #{request_obj.id}"
        subject = f"{subject_prefix}עדכון בקשה"

    for user in app_notification_recipients:
        Notification.objects.create(
            user=user,
            message=message,
            created_at=timezone.now(),
            read=False
        )
        logger.debug(f"🟢 התראה נוצרה עבור {user.username}")

    html_message = render_to_string('request_notification_email.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            html_message=html_message,
            fail_silently=False
        )
        logger.debug(f"📧 נשלח מייל ל־{recipients}")
    except Exception as e:
        logger.debug(f"❌ שגיאה בשליחת מייל: {e}")
        

# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.urls import reverse
# from django.utils.html import strip_tags

# def send_request_notification(request_obj, notification_type, recipient=None):

#     # Get base URL for links
#     base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
#     request_url = f"{base_url}{reverse('request_detail', args=[request_obj.id])}"

#     context = {
#         'request': request_obj,
#         'request_url': request_url,
#         'notification_type': notification_type,
#     }

#     # Determine recipients based on notification type
#     if recipient is None:
#         if notification_type == 'created':
#             # Notify all assigned users
#             recipients = [user.email for user in request_obj.assigned_to.all() if user.email]
#         elif notification_type in ['updated', 'resolved', 'info_requested']:
#             # Notify the student
#             recipients = [request_obj.student.email]
#         elif notification_type == 'comment':
#             # If comment is from student, notify assigned users
#             # If comment is from staff, notify student
#             latest_comment = request_obj.comments.latest('created')
#             if latest_comment.user == request_obj.student:
#                 recipients = [user.email for user in request_obj.assigned_to.all() if user.email]
#             else:
#                 recipients = [request_obj.student.email]
#         else:
#             recipients = []
#     else:
#         # Send to specific recipient
#         recipients = [recipient.email] if hasattr(recipient, 'email') else [recipient]

#     # Don't proceed if no recipients
#     if not recipients:
#         return

#     # Determine subject based on notification type
#     subject_prefix = 'EasyREQ - '
#     if notification_type == 'created':
#         subject = f"{subject_prefix}New Request #{request_obj.id}: {request_obj.get_title_display()}"
#     elif notification_type == 'updated':
#         subject = f"{subject_prefix}Request #{request_obj.id} Status Updated"
#     elif notification_type == 'comment':
#         subject = f"{subject_prefix}New Comment on Request #{request_obj.id}"
#     elif notification_type == 'resolved':
#         status = 'Approved' if request_obj.status == 1 else 'Rejected'
#         subject = f"{subject_prefix}Request #{request_obj.id} {status}"
#     elif notification_type == 'info_requested':
#         subject = f"{subject_prefix}Additional Information Needed for Request #{request_obj.id}"
#     elif notification_type == 'assigned':
#         subject = f"{subject_prefix}Request #{request_obj.id} Assigned to You"
#     else:
#         subject = f"{subject_prefix}Request #{request_obj.id} Update"

#     # Render email content
#     html_message = render_to_string('request_notification_email.html', context)
#     plain_message = strip_tags(html_message)

#     # Send the email
#     try:
#         send_mail(
#             subject,
#             plain_message,
#             settings.DEFAULT_FROM_EMAIL,
#             recipients,
#             html_message=html_message,
#             fail_silently=False
#         )
#         print(f"Email notification sent to {recipients} for request #{request_obj.id}")
#     except Exception as e:
#         print(f"Failed to send email notification: {e}")
