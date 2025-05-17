# from Website.models import Request, User

# def global_notifications(request):
#     notifications = []
#     notification_count = 0
#     user = request.user

#     if user.is_authenticated:
#         role = user.role

#         if role == 2:  # מזכירות
#             # רק בקשות ממחלקה של המזכירה
#             new_requests = Request.objects.filter(status=0, dept=user.department).count()
#             pending_lecturers = User.objects.filter(role=1, is_active=False, department=user.department).count()

#             if new_requests:
#                 notifications.append({
#                     "message": f"{new_requests} בקשות חדשות ממתינות במחלקתך",
#                     "time": ""
#                 })
#                 notification_count += new_requests

#             if pending_lecturers:
#                 notifications.append({
#                     "message": f"{pending_lecturers} מרצים ממחלקתך ממתינים לאישור",
#                     "time": ""
#                 })
#                 notification_count += pending_lecturers

#         elif role == 1:  # מרצה
#             if not user.is_active:
#                 notifications.append({
#                     "message": "החשבון שלך עדיין ממתין לאישור",
#                     "time": ""
#                 })
#                 notification_count += 1
#             else:
#                 assigned_requests = Request.objects.filter(assigned_to=user, status=0).count()
#                 if assigned_requests:
#                     notifications.append({
#                         "message": f"{assigned_requests} בקשות חדשות הוקצו אליך",
#                         "time": ""
#                     })
#                     notification_count += assigned_requests

#         elif role == 3:  # דיקאנט
#             new_requests = Request.objects.filter(status=0).count()
#             if new_requests:
#                 notifications.append({
#                     "message": f"{new_requests} בקשות חדשות ממתינות לבדיקה",
#                     "time": ""
#                 })
#                 notification_count += new_requests

#         elif role == 0:  # סטודנט
#             student_requests = Request.objects.filter(student=user).order_by('-modified')[:5]
#             for req in student_requests:
#                 notifications.append({
#                     "message": f"הבקשה #{req.id} - {req.get_status_display()}",
#                     "time": req.modified.strftime("%d/%m/%Y %H:%M") if req.modified else ""
#                 })
#                 notification_count += 1

#     return {
#         'notifications': notifications,
#         'notification_count': notification_count,
#         'role': user.role if user.is_authenticated else 0
#     }

from Website.models import Notification

def global_notifications(request):
    """
    Context processor שמוסיף התראות מהדאטאבייס לכל התבניות
    """
    user = request.user
    notifications = []
    notification_count = 0
    
    if user.is_authenticated:
        # קבלת התראות מהדאטאבייס
        notifications = Notification.objects.filter(
            user=user,
            read=False
        ).order_by('-created_at')
        
        notification_count = notifications.count()
        
    return {
        'notifications': notifications,
        'notification_count': notification_count,
        'role': user.role if user.is_authenticated else 0
    }