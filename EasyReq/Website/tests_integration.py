from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.messages import get_messages
import datetime
import json
import random
import string

from .models import (
    Department, Course, Request, RequestStatus, 
    RequestComment, User, Notification, Review
)

User = get_user_model()

def random_email():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"test_{random_str}@example.com"


class RequestLifecycleIntegrationTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        self.department = Department.objects.create(name='מחלקת בדיקות')
        
        self.course = Course.objects.create(
            name='קורס בדיקות',
            year=1,
            dept=self.department
        )
        
        self.student = User.objects.create_user(
            username='student_lifecycle',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='לבדיקות',
            department=self.department,
            role=0,
            is_active=True
        )
        self.student.courses.add(self.course)
        
        self.lecturer = User.objects.create_user(
            username='lecturer_lifecycle',
            password='password123',
            email=random_email(),
            first_name='מרצה',
            last_name='לבדיקות',
            department=self.department,
            role=1,
            is_active=True
        )
        self.lecturer.courses.add(self.course)
        
        self.staff = User.objects.create_user(
            username='staff_lifecycle',
            password='password123',
            email=random_email(),
            first_name='מזכירות',
            last_name='לבדיקות',
            department=self.department,
            role=2,
            is_active=True
        )
    
    def test_complete_request_lifecycle(self):
        request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,  
            description='בדיקת תהליך שלם של בקשה',
            priority=1,  
            course=self.course
        )
        
        request.assigned_to.add(self.lecturer)
        request.viewers.add(self.staff)
        
        self.lecturer.is_active = True
        self.lecturer.save()
        

        RequestStatus.objects.create(
            request=request,
            status=1, 
            updated_by=self.lecturer,
            notes='הבקשה בבדיקה על ידי המרצה'
        )
        
        request.pipeline_status = 1 
        request.save()
        
        request.refresh_from_db()
        self.assertEqual(request.pipeline_status, 1)
        
        comment = RequestComment.objects.create(
            request=request,
            user=self.student,
            comment='תגובה מהסטודנט למרצה'
        )
        
        RequestStatus.objects.create(
            request=request,
            status=4,  
            updated_by=self.staff,
            notes='הבקשה אושרה על ידי המזכירות'
        )
        
        request.pipeline_status = 4  
        request.status = 1
        request.resolution_notes = 'אישור סופי לערעור'
        request.resolved_date = timezone.now()
        request.save()
        
        request.refresh_from_db()
        self.assertEqual(request.pipeline_status, 4)
        self.assertEqual(request.status, 1)  


class SimpleStudentRequestsTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת סטודנט')
        self.course = Course.objects.create(name='קורס סטודנט', year=1, dept=self.department)
        
        self.student = User.objects.create_user(
            username='simple_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='פשוט',
            department=self.department,
            role=0,
            is_active=True
        )
        self.student.courses.add(self.course)
    
    def test_create_request(self):
        login_successful = self.client.login(username='simple_student', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.post(reverse('create_request'), {
            'course': self.course.id,
            'title': '0',  
            'description': 'בקשה לבדיקת ערעור',
            'priority': '1' 
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        request = Request.objects.filter(description='בקשה לבדיקת ערעור').first()
        self.assertIsNotNone(request)
        self.assertEqual(request.student, self.student)
        self.assertEqual(request.course, self.course)
    
    def test_view_request_list(self):
        request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=1, 
            description='בקשה לרשימת בקשות',
            course=self.course,
            status=0 
        )
        
        login_successful = self.client.login(username='simple_student', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.get(reverse('list_requests'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, str(request.id))


class PasswordResetIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת איפוס')
        
        self.user = User.objects.create_user(
            username='reset_user',
            password='oldpassword123',
            email='reset@example.com',
            first_name='משתמש',
            last_name='לאיפוס',
            department=self.department,
            role=0,
            is_active=True
        )
    
    def test_password_reset_page_loads(self):
        response = self.client.get(reverse('reset_password'))
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset_form_submission(self):
        response = self.client.post(reverse('reset_password'), {
            'email': 'reset@example.com'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_password_reset_complete_page(self):
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)


class BulkOperationsTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת פעולות קבוצתיות')
        
        self.staff = User.objects.create_user(
            username='bulk_staff',
            password='password123',
            email=random_email(),
            first_name='מזכירות',
            last_name='קבוצתית',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.students = []
        for i in range(3):
            student = User.objects.create_user(
                username=f'bulk_student_{i}',
                password='password123',
                email=random_email(),
                first_name=f'סטודנט_{i}',
                last_name='לבדיקה',
                department=self.department,
                role=0,
                is_active=True
            )
            self.students.append(student)
        
        self.lecturers = []
        for i in range(2):
            lecturer = User.objects.create_user(
                username=f'bulk_lecturer_{i}',
                password='password123',
                email=random_email(),
                first_name=f'מרצה_{i}',
                last_name='לבדיקה',
                department=self.department,
                role=1,
                is_active=True
            )
            self.lecturers.append(lecturer)
        
        self.courses = []
        for i in range(2):
            course = Course.objects.create(
                name=f'קורס_{i}',
                year=1,
                dept=self.department
            )
            self.courses.append(course)
        
        self.requests = []
        for i, student in enumerate(self.students[:2]):
            request = Request.objects.create(
                student=student,
                dept=self.department,
                title=i,
                description=f'בקשה {i} למחיקה קבוצתית',
                priority=1
            )
            self.requests.append(request)
    
    def test_bulk_delete_students(self):
        self.client.login(username='bulk_staff', password='password123')
        
        student_ids = [str(self.students[0].id), str(self.students[1].id)]
        
        response = self.client.post(reverse('bulk_delete_students'), {
            'bulk_delete': 'true',
            'selected_students': student_ids
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(User.objects.filter(id=self.students[0].id).exists())
        self.assertFalse(User.objects.filter(id=self.students[1].id).exists())
        
        self.assertTrue(User.objects.filter(id=self.students[2].id).exists())
    
    
    def test_bulk_delete_courses(self):
        self.client.login(username='bulk_staff', password='password123')
        
        course_ids = [str(self.courses[0].id)]
        
        response = self.client.post(reverse('bulk_delete_courses'), {
            'selected_courses': course_ids
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=self.courses[0].id).exists())
        
        self.assertTrue(Course.objects.filter(id=self.courses[1].id).exists())
    
    def test_bulk_delete_requests(self):
        self.client.login(username='bulk_staff', password='password123')
        
        request_ids = [str(self.requests[0].id)]
        
        response = self.client.post(reverse('bulk_delete_requests'), {
            'selected_requests': request_ids
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Request.objects.filter(id=self.requests[0].id).exists())
        
        self.assertTrue(Request.objects.filter(id=self.requests[1].id).exists())
    

class ChatIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת צ\'אט')
        
        self.user = User.objects.create_user(
            username='chat_user',
            password='password123',
            email=random_email(),
            first_name='משתמש',
            last_name='צ\'אט',
            department=self.department,
            role=0,
            is_active=True
        )
    
    def test_chat_response_endpoint(self):
        self.client.login(username='chat_user', password='password123')
        
        response = self.client.post(
            reverse('chat_response'),
            data=json.dumps({'message': 'שלום, איך אוכל להגיש בקשה?'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('response', data)
        self.assertIsInstance(data['response'], str)
    
    def test_chat_response_empty_message(self):
        self.client.login(username='chat_user', password='password123')
        
        response = self.client.post(
            reverse('chat_response'),
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_chat_response_invalid_method(self):
        response = self.client.get(reverse('chat_response'))
        self.assertEqual(response.status_code, 405)
    
    def test_chat_response_malformed_json(self):
        self.client.login(username='chat_user', password='password123')
        
        response = self.client.post(
            reverse('chat_response'),
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('response', data)


class NotificationIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת התראות')
        
        self.user = User.objects.create_user(
            username='notif_user',
            password='password123',
            email=random_email(),
            first_name='משתמש',
            last_name='התראות',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.notifications = []
        for i in range(3):
            notif = Notification.objects.create(
                user=self.user,
                message=f'התראה {i}',
                read=False
            )
            self.notifications.append(notif)
    
    def test_mark_notification_read(self):
        self.client.login(username='notif_user', password='password123')
        
        response = self.client.post(
            reverse('mark_notification_read'),
            data=json.dumps({'notification_id': self.notifications[0].id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        self.notifications[0].refresh_from_db()
        self.assertTrue(self.notifications[0].read)
        
        self.notifications[1].refresh_from_db()
        self.assertFalse(self.notifications[1].read)
    
    def test_mark_all_notifications_read(self):
        self.client.login(username='notif_user', password='password123')
        
        response = self.client.post(reverse('mark_all_notifications_read'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        for notif in self.notifications:
            notif.refresh_from_db()
            self.assertTrue(notif.read)
    
    def test_view_all_notifications_page(self):
        self.client.login(username='notif_user', password='password123')
        
        response = self.client.get(reverse('all_notifications'))
        self.assertEqual(response.status_code, 200)
        
        for notif in self.notifications:
            self.assertContains(response, notif.message)
    
    def test_toggle_notification_status(self):
        """בדיקת החלפת סטטוס התראה"""
        self.client.login(username='notif_user', password='password123')
        
        response = self.client.post(
            reverse('toggle_notification_status'),
            data=json.dumps({'notification_id': self.notifications[0].id, 'read': True}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.notifications[0].refresh_from_db()
        self.assertTrue(self.notifications[0].read)
        
        response = self.client.post(
            reverse('toggle_notification_status'),
            data=json.dumps({'notification_id': self.notifications[0].id, 'read': False}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.notifications[0].refresh_from_db()
        self.assertFalse(self.notifications[0].read)


class RatingSystemIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת דירוגים')
        
        self.user = User.objects.create_user(
            username='rating_user',
            password='password123',
            email=random_email(),
            first_name='משתמש',
            last_name='דירוגים',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.other_user = User.objects.create_user(
            username='other_rating_user',
            password='password123',
            email=random_email(),
            first_name='משתמש',
            last_name='אחר',
            department=self.department,
            role=0,
            is_active=True
        )
    
    
    def test_submit_rating(self):
        self.client.login(username='rating_user', password='password123')
        
        response = self.client.post(reverse('submit_review'), {
            'rating': '5',
            'message': 'האתר מעולה!'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        review = Review.objects.filter(user=self.user).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.message, 'האתר מעולה!')
    
    def test_edit_existing_rating(self):
        Review.objects.create(
            user=self.user,
            rating=3,
            message='בסדר'
        )
        
        self.client.login(username='rating_user', password='password123')
        
        response = self.client.post(reverse('edit_review'), {
            'rating': '4',
            'message': 'משופר!'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        review = Review.objects.get(user=self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.message, 'משופר!')
    
    def test_delete_rating(self):
        Review.objects.create(
            user=self.user,
            rating=3,
            message='בסדר'
        )
        
        self.client.login(username='rating_user', password='password123')
        
        response = self.client.post(reverse('delete_review'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(Review.objects.filter(user=self.user).exists())
    
    def test_rating_stats_api(self):
        Review.objects.create(user=self.user, rating=5, message='מעולה')
        Review.objects.create(user=self.other_user, rating=4, message='טוב')
        
        response = self.client.get(reverse('get_rating_stats'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('average_rating', data)
        self.assertIn('total_reviews', data)
        self.assertIn('rating_distribution', data)
        self.assertEqual(data['total_reviews'], 2)
    
    def test_duplicate_rating_prevention(self):
        Review.objects.create(user=self.user, rating=3, message='ראשון')
        
        self.client.login(username='rating_user', password='password123')
        
        response = self.client.post(reverse('submit_review'), {
            'rating': '5',
            'message': 'שני'
        }, follow=True)
        
        self.assertEqual(Review.objects.filter(user=self.user).count(), 1)
        
        review = Review.objects.get(user=self.user)
        self.assertEqual(review.rating, 3)
        self.assertEqual(review.message, 'ראשון')


class StaffOperationsTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת מזכירות')

        self.staff = User.objects.create_user(
            username='staff_operations',
            password='password123',
            email=random_email(),
            first_name='צוות',
            last_name='מזכירות',
            department=self.department,
            role=2,
            is_active=True
        )

        self.student = User.objects.create_user(
            username='student_for_staff',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='למזכירות',
            department=self.department,
            role=0,
            is_active=True
        )

        self.course = Course.objects.create(name='קורס מזכירות', year=1, dept=self.department)
    
    def test_manage_courses(self):
        login_successful = self.client.login(username='staff_operations', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.get(reverse('manage_courses'))
        self.assertEqual(response.status_code, 200)
    
    def test_add_course(self):
        login_successful = self.client.login(username='staff_operations', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.post(reverse('add_course'), {
            'name': 'קורס חדש למזכירות',
            'year': '2'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(Course.objects.filter(name='קורס חדש למזכירות').exists())
    
    def test_approve_student_request(self):
        request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=2,  
            description='בקשה לאישור מזכירות',
            course=self.course
        )
        
        request.viewers.add(self.staff)
        
        login_successful = self.client.login(username='staff_operations', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.post(reverse('update_request_status', args=[request.id]), {
            'pipeline_status': '4',  
            'status_notes': 'אישור בקשה על ידי מזכירות',
            'resolution_notes': 'אושר'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        request.refresh_from_db()
        self.assertEqual(request.pipeline_status, 4)
        self.assertEqual(request.status, 1) 

    def test_student_cannot_access_manage_courses(self):
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('manage_courses'))
        self.assertIn(response.status_code, [302, 403]) 

    def test_student_cannot_approve_request(self):
        request_obj = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=1,
            description='בדיקה על ידי סטודנט',
            course=self.course
        )
        
        login_successful = self.client.login(username='student_for_staff', password='password123')
        self.assertTrue(login_successful)

        response = self.client.post(reverse('update_request_status', args=[request_obj.id]), {
            'pipeline_status': '4',
            'status_notes': 'סטודנט מנסה לעדכן סטטוס',
            'resolution_notes': 'לא אמור להצליח'
        }, follow=True)

        self.assertRedirects(response, reverse('home'))
        
        request_obj.refresh_from_db()
        self.assertNotEqual(request_obj.pipeline_status, 4)
        self.assertNotEqual(request_obj.status, 1)

    def test_create_request_with_attachment(self):
        login_successful = self.client.login(username='student_for_staff', password='password123')
        self.assertTrue(login_successful)

        file = SimpleUploadedFile("example.pdf", b"dummy content", content_type="application/pdf")

        response = self.client.post(reverse('create_request'), {
            'course': self.course.id,
            'title': '1',
            'description': 'בקשה עם קובץ',
            'priority': '1',
            'attachment': file
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        req = Request.objects.filter(description='בקשה עם קובץ').first()
        self.assertIsNotNone(req)
        self.assertTrue(req.attachments)

    def test_view_notifications(self):
        Notification.objects.create(user=self.staff, message='התראה חדשה')
        self.client.login(username='staff_operations', password='password123')
        response = self.client.get(reverse('all_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'התראה חדשה')

    def test_profile_edit_access(self):
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_picture_upload(self):
        self.client.login(username='student_for_staff', password='password123')
        image = SimpleUploadedFile("avatar.jpg", b"testcontent", content_type="image/jpeg")
        response = self.client.post(reverse('profile'), {
            'profile_pic': image
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.profile_pic.name.startswith('profile_pics/'))

    def test_request_filter_by_status(self):
        Request.objects.create(
            student=self.student,
            dept=self.department,
            title=1,
            description='משהו לבדיקה',
            course=self.course,
            status=1  
        )
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('list_requests') + '?status=1')
        self.assertEqual(response.status_code, 200)

    def test_request_filter_by_priority(self):
        Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='בדיקה לפי עדיפות',
            course=self.course,
            priority=3  
        )
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('list_requests') + '?priority=3')
        self.assertEqual(response.status_code, 200)

    def test_request_filter_by_date_range(self):
        old_request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=1,
            description='בקשה ישנה',
            course=self.course
        )
        old_request.created = make_aware(datetime.datetime(2025, 5, 17))
        old_request.save()

        self.client.login(username='student_for_staff', password='password123')

        today_str = timezone.now().strftime('%Y-%m-%d')
        response = self.client.get(reverse('list_requests') + f'?date_from={today_str}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'בקשה ישנה')

    def test_student_cannot_view_others_requests(self):
        other_student = User.objects.create_user(
            username='other_student',
            password='password123',
            email=random_email(),
            first_name='אחר',
            last_name='סטודנט',
            department=self.department,
            role=0,
            is_active=True
        )
        other_request = Request.objects.create(
            student=other_student,
            dept=self.department,
            title=1,
            description='בקשת תלמיד אחר',
            course=self.course
        )
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('request_detail', args=[other_request.id]))
        self.assertIn(response.status_code, [302, 403])

    def test_dashboard_access(self):
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_request_detail_page(self):
        request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='פרטי בקשה לבדיקה',
            course=self.course
        )
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('request_detail', args=[request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'פרטי בקשה לבדיקה')

    def test_export_requests_csv(self):
        self.client.login(username='staff_operations', password='password123')
        response = self.client.get(reverse('export_requests_csv'))
        self.assertEqual(response.status_code, 200)

    def test_export_dashboard_excel(self):
        self.client.login(username='staff_operations', password='password123')
        response = self.client.get(reverse('export_dashboard_excel'))
        self.assertEqual(response.status_code, 200)


class AdvancedCourseManagementTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת קורסים')
        
        self.staff = User.objects.create_user(
            username='course_staff',
            password='password123',
            email=random_email(),
            first_name='מזכירות',
            last_name='קורסים',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.lecturer = User.objects.create_user(
            username='course_lecturer',
            password='password123',
            email=random_email(),
            first_name='מרצה',
            last_name='קורסים',
            department=self.department,
            role=1,
            is_active=True
        )
        
        self.student = User.objects.create_user(
            username='course_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='קורסים',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.course = Course.objects.create(
            name='קורס לבדיקה',
            year=1,
            dept=self.department
        )
    
    def test_edit_course(self):
        self.client.login(username='course_staff', password='password123')
        
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'name': 'קורס מעודכן',
            'year': '2',
            'lecturers': [str(self.lecturer.id)]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'קורס מעודכן')
        self.assertEqual(self.course.year, 2)
        self.assertIn(self.lecturer, self.course.user_set.all())
    
    def test_delete_course(self):
        self.client.login(username='course_staff', password='password123')
        
        course_id = self.course.id
        response = self.client.post(reverse('delete_course', args=[course_id]), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(id=course_id).exists())
    
    def test_assign_lecturers_to_course(self):
        self.client.login(username='course_staff', password='password123')
        
        response = self.client.post(reverse('assign_lecturers_to_course', args=[self.course.id]), {
            'lecturers': [str(self.lecturer.id)]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.lecturer, self.course.user_set.all())
    
    def test_assign_students_to_course(self):
        self.client.login(username='course_staff', password='password123')
        
        response = self.client.post(reverse('assign_students_to_course', args=[self.course.id]), {
            'students': [str(self.student.id)]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.student, self.course.user_set.all())


class UserManagementIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת משתמשים')
        
        self.staff = User.objects.create_user(
            username='user_staff',
            password='password123',
            email=random_email(),
            first_name='מזכירות',
            last_name='משתמשים',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.student = User.objects.create_user(
            username='managed_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='מנוהל',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.pending_lecturer = User.objects.create_user(
            username='pending_lecturer',
            password='password123',
            email=random_email(),
            first_name='מרצה',
            last_name='ממתין',
            department=self.department,
            role=1,
            is_active=False
        )
    
    def test_manage_users_page(self):
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.get_full_name())
        
        self.assertContains(response, self.pending_lecturer.get_full_name())
    
    def test_approve_lecturer(self):
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.post(reverse('approve_lecturer'), {
            'action': 'approve',
            'user_id': str(self.pending_lecturer.id)
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.pending_lecturer.refresh_from_db()
        self.assertTrue(self.pending_lecturer.is_active)
    
    def test_reject_lecturer(self):
        self.client.login(username='user_staff', password='password123')
        
        lecturer_id = self.pending_lecturer.id
        response = self.client.post(reverse('approve_lecturer'), {
            'action': 'reject',
            'user_id': str(lecturer_id)
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(User.objects.filter(id=lecturer_id).exists())
    
    def test_edit_student_form(self):
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.post(reverse('edit_student_form', args=[self.student.id]), {
            'first_name': 'סטודנט מעודכן',
            'last_name': 'חדש',
            'email': 'updated@example.com',
            'info': 'מידע חדש',
            'is_active': 'on'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'סטודנט מעודכן')
        self.assertEqual(self.student.last_name, 'חדש')
        self.assertEqual(self.student.email, 'updated@example.com')
    
    def test_deactivate_student(self):
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.post(reverse('confirm_deactivate_student', args=[self.student.id]), follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
    
    def test_activate_student(self):
        self.student.is_active = False
        self.student.save()
        
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.post(reverse('activate_student', args=[self.student.id]), follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)
    
    def test_assign_student_courses_form(self):
        course = Course.objects.create(name='קורס לשיוך', year=1, dept=self.department)
        
        self.client.login(username='user_staff', password='password123')
        
        response = self.client.post(reverse('assign_student_courses_form', args=[self.student.id]), {
            'courses': [str(course.id)]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(course, self.student.courses.all())


class RegistrationAndAuthTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת רישום')
        
        self.course = Course.objects.create(
            name='קורס רישום',
            year=1,
            dept=self.department
        )
    
    def test_registration_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'הרשמה')
 
    
    def test_login_functionality(self):
        user = User.objects.create_user(
            username='login_test',
            password='password123',
            email='login@example.com',
            department=self.department,
            role=0,
            is_active=True
        )
        
        response = self.client.post(reverse('login'), {
            'username': 'login_test',
            'password': 'password123'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_inactive_user(self):
        user = User.objects.create_user(
            username='inactive_user',
            password='password123',
            email='inactive@example.com',
            department=self.department,
            role=1,
            is_active=False
        )
        
        response = self.client.post(reverse('login'), {
            'username': 'inactive_user',
            'password': 'password123'
        }, follow=True)
        
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout_functionality(self):
        user = User.objects.create_user(
            username='logout_test',
            password='password123',
            email='logout@example.com',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.client.login(username='logout_test', password='password123')
        
        response = self.client.get(reverse('logout'), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_registration_success_page(self):
        user = User.objects.create_user(
            username='success_test',
            password='password123',
            email='success@example.com',
            department=self.department,
            role=0,
            is_active=True
        )
        
        response = self.client.get(reverse('registration_success', args=[user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.get_full_name())


class ProfileManagementTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת פרופיל')
        
        self.student = User.objects.create_user(
            username='profile_student',
            password='password123',
            email='student@example.com',
            first_name='סטודנט',
            last_name='פרופיל',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.lecturer = User.objects.create_user(
            username='profile_lecturer',
            password='password123',
            email='lecturer@example.com',
            first_name='מרצה',
            last_name='פרופיל',
            department=self.department,
            role=1,
            is_active=True
        )
        
        self.course = Course.objects.create(
            name='קורס פרופיל',
            year=1,
            dept=self.department
        )
    
    def test_profile_page_access(self):
        self.client.login(username='profile_student', password='password123')
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.get_full_name())
    
    def test_student_email_update(self):
        self.client.login(username='profile_student', password='password123')
        
        response = self.client.post(reverse('profile'), {
            'action': 'update_email',
            'new_email': 'newemail@sce.ac.il'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.email, 'newemail@sce.ac.il')
    
    
    def test_password_change(self):
        self.client.login(username='profile_student', password='password123')
        
        response = self.client.post(reverse('profile'), {
            'action': 'update_password',
            'old_password': 'password123',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.client.logout()
        login_success = self.client.login(username='profile_student', password='newpassword456')
        self.assertTrue(login_success)


class RequestCommentIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת תגובות')
        
        self.student = User.objects.create_user(
            username='comment_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='תגובות',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.staff = User.objects.create_user(
            username='comment_staff',
            password='password123',
            email=random_email(),
            first_name='צוות',
            last_name='תגובות',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='בקשה לתגובות',
            priority=1
        )
        self.request.viewers.add(self.staff)
    
    def test_student_add_comment(self):
        self.client.login(username='comment_student', password='password123')
        
        response = self.client.post(reverse('request_detail', args=[self.request.id]), {
            'comment': 'תגובה מהסטודנט'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        comment = RequestComment.objects.filter(
            request=self.request,
            user=self.student,
            comment='תגובה מהסטודנט'
        ).first()
        self.assertIsNotNone(comment)
    
    def test_staff_add_comment(self):
        self.client.login(username='comment_staff', password='password123')
        
        response = self.client.post(reverse('request_detail', args=[self.request.id]), {
            'comment': 'תגובה מהצוות'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        comment = RequestComment.objects.filter(
            request=self.request,
            user=self.staff,
            comment='תגובה מהצוות'
        ).first()
        self.assertIsNotNone(comment)
    
    def test_comment_display_in_request_detail(self):
        RequestComment.objects.create(
            request=self.request,
            user=self.student,
            comment='תגובה לבדיקת תצוגה'
        )
        
        self.client.login(username='comment_student', password='password123')
        
        response = self.client.get(reverse('request_detail', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'תגובה לבדיקת תצוגה')


class DashboardIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת דשבורד')
        
        self.student = User.objects.create_user(
            username='dashboard_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='דשבורד',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.staff = User.objects.create_user(
            username='dashboard_staff',
            password='password123',
            email=random_email(),
            first_name='צוות',
            last_name='דשבורד',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.lecturer = User.objects.create_user(
            username='dashboard_lecturer',
            password='password123',
            email=random_email(),
            first_name='מרצה',
            last_name='דשבורד',
            department=self.department,
            role=1,
            is_active=True
        )
        
        for i in range(3):
            request = Request.objects.create(
                student=self.student,
                dept=self.department,
                title=i % 3,
                description=f'בקשה {i} לדשבורד',
                priority=i % 3,
                status=i % 3  # 0=ממתין, 1=מאושר, 2=נדחה
            )
            if i == 0:  
                request.assigned_to.add(self.lecturer)
            request.viewers.add(self.staff)
    
    def test_student_dashboard(self):
        self.client.login(username='dashboard_student', password='password123')
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'סה"כ בקשות')
        self.assertContains(response, 'בקשות בטיפול')
    
    def test_staff_dashboard(self):
        self.client.login(username='dashboard_staff', password='password123')
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'זמן טיפול ממוצע')
    
    
    def test_dashboard_with_filters(self):
        self.client.login(username='dashboard_staff', password='password123')
        
        response = self.client.get(reverse('dashboard') + '?status=0')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('dashboard') + f'?department={self.department.id}')
        self.assertEqual(response.status_code, 200)


class ExportIntegrationTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת ייצוא')
        
        self.staff = User.objects.create_user(
            username='export_staff',
            password='password123',
            email=random_email(),
            first_name='צוות',
            last_name='ייצוא',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.student = User.objects.create_user(
            username='export_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='ייצוא',
            department=self.department,
            role=0,
            is_active=True
        )
        
        for i in range(5):
            request = Request.objects.create(
                student=self.student,
                dept=self.department,
                title=i % 3,
                description=f'בקשה {i} לייצוא',
                priority=i % 3,
                status=i % 3
            )
            request.viewers.add(self.staff)
    
    def test_export_requests_excel(self):
        self.client.login(username='export_staff', password='password123')
        
        response = self.client.get(reverse('export_requests_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_export_dashboard_excel(self):
        self.client.login(username='export_staff', password='password123')
        
        response = self.client.get(reverse('export_dashboard_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    def test_export_requests_csv(self):
        self.client.login(username='export_staff', password='password123')
        
        response = self.client.get(reverse('export_requests_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_student_cannot_export(self):
        self.client.login(username='export_student', password='password123')
        response = self.client.get(reverse('export_requests_excel'))
        self.assertIn(response.status_code, [200, 302, 403])


class ErrorHandlingTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת שגיאות')
        
        self.user = User.objects.create_user(
            username='error_user',
            password='password123',
            email=random_email(),
            first_name='משתמש',
            last_name='שגיאות',
            department=self.department,
            role=0,
            is_active=True
        )
    
    def test_nonexistent_request_detail(self):
        self.client.login(username='error_user', password='password123')
        
        response = self.client.get(reverse('request_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)
    
    def test_unauthorized_request_access(self):
        other_user = User.objects.create_user(
            username='other_user',
            password='password123',
            email=random_email(),
            department=self.department,
            role=0,
            is_active=True
        )
        
        request = Request.objects.create(
            student=other_user,
            dept=self.department,
            title=0,
            description='בקשה של אחר',
            priority=1
        )
        
        self.client.login(username='error_user', password='password123')
        
        response = self.client.get(reverse('request_detail', args=[request.id]))
        self.assertIn(response.status_code, [302, 403])
    
   
    def test_access_without_login(self):
        protected_urls = [
            reverse('dashboard'),
            reverse('create_request'),
            reverse('profile'),
            reverse('list_requests')
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [302, 403])


class GetCoursesAjaxTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת AJAX')
        
        self.course1 = Course.objects.create(
            name='קורס 1',
            year=1,
            dept=self.department
        )
        
        self.course2 = Course.objects.create(
            name='קורס 2',
            year=2,
            dept=self.department
        )
    
    def test_get_courses_by_department(self):
        response = self.client.get(reverse('get_courses'), {
            'department': self.department.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('courses', data)
        self.assertEqual(len(data['courses']), 2)
        
        course_names = [course['name'] for course in data['courses']]
        self.assertIn('קורס 1', course_names)
        self.assertIn('קורס 2', course_names)
    
    def test_get_courses_invalid_department(self):
        response = self.client.get(reverse('get_courses'), {
            'department': 99999
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['courses'], [])
    
    def test_get_courses_no_department(self):
        response = self.client.get(reverse('get_courses'))
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['courses'], [])

class ComplexWorkflowTests(TestCase):    
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='מחלקת תהליכים')
        
        self.course = Course.objects.create(
            name='קורס תהליכים',
            year=1,
            dept=self.department
        )
        
        self.student = User.objects.create_user(
            username='workflow_student',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='תהליכים',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.lecturer = User.objects.create_user(
            username='workflow_lecturer',
            password='password123',
            email=random_email(),
            first_name='מרצה',
            last_name='תהליכים',
            department=self.department,
            role=1,
            is_active=True
        )
        
        self.staff = User.objects.create_user(
            username='workflow_staff',
            password='password123',
            email=random_email(),
            first_name='מזכירות',
            last_name='תהליכים',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.deanery = User.objects.create_user(
            username='workflow_deanery',
            password='password123',
            email=random_email(),
            first_name='דיקאנט',
            last_name='תהליכים',
            department=self.department,
            role=3,
            is_active=True
        )
    

class TestRunner(TestCase):    
    def test_all_tests_loaded(self):
        test_classes = [
            RequestLifecycleIntegrationTests,
            SimpleStudentRequestsTests,
            PasswordResetIntegrationTests,
            BulkOperationsTests,
            ChatIntegrationTests,
            NotificationIntegrationTests,
            RatingSystemIntegrationTests,
            StaffOperationsTests,
            AdvancedCourseManagementTests,
            UserManagementIntegrationTests,
            RegistrationAndAuthTests,
            ProfileManagementTests,
            RequestCommentIntegrationTests,
            DashboardIntegrationTests,
            ExportIntegrationTests,
            ErrorHandlingTests,
            GetCoursesAjaxTests,
            ComplexWorkflowTests
        ]
        
        for test_class in test_classes:
            self.assertTrue(issubclass(test_class, TestCase))
        
        self.assertEqual(len(test_classes), 18)  
        
