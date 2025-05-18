from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.timezone import make_aware
import datetime
import json
import random
import string

from .models import (
    Department, Course, Request, RequestStatus, 
    RequestComment, User, Notification
)

User = get_user_model()

def random_email():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"test_{random_str}@example.com"


class RequestLifecycleIntegrationTests(TestCase):
    """בדיקות אינטגרציה לתהליך חיים שלם של בקשה"""
    
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
        """
        בדיקת תהליך שלם של בקשה:
        1. יצירת בקשה ישירות
        2. בדיקת עדכון סטטוס
        3. הוספת תגובה ישירות
        4. אישור סופי
        """
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
    """בדיקות פשוטות ליצירת וצפייה בבקשות"""
    
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
        """בדיקה שסטודנט יכול ליצור בקשה"""
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
        """בדיקה שסטודנט יכול לצפות ברשימת הבקשות שלו"""
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


class StaffOperationsTests(TestCase):
    """בדיקות פעולות צוות מזכירות"""
    
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

        self.staff_extra = User.objects.create_user(
            username='staff_extra',
            password='password123',
            email=random_email(),
            first_name='צוות',
            last_name='נוסף',
            department=self.department,
            role=2,
            is_active=True
        )

        self.student_extra = User.objects.create_user(
            username='student_extra',
            password='password123',
            email=random_email(),
            first_name='סטודנט',
            last_name='נוסף',
            department=self.department,
            role=0,
            is_active=True
        )

        self.course = Course.objects.create(name='קורס מזכירות', year=1, dept=self.department)
    
    def test_manage_courses(self):
        """בדיקה שמזכירות יכולה לצפות בדף ניהול הקורסים"""
        login_successful = self.client.login(username='staff_operations', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.get(reverse('manage_courses'))
        self.assertEqual(response.status_code, 200)
    
    def test_add_course(self):
        """בדיקה שמזכירות יכולה להוסיף קורס חדש"""
        login_successful = self.client.login(username='staff_operations', password='password123')
        self.assertTrue(login_successful)
        
        response = self.client.post(reverse('add_course'), {
            'name': 'קורס חדש למזכירות',
            'year': '2'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(Course.objects.filter(name='קורס חדש למזכירות').exists())
    
    def test_approve_student_request(self):
        """בדיקה שמזכירות יכולה לאשר בקשה של סטודנט"""
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
        """בדיקה שסטודנט לא יכול לגשת לדף ניהול הקורסים"""
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('manage_courses'))
        self.assertIn(response.status_code, [302, 403]) 

    def test_student_cannot_approve_request(self):
        """בדיקה שסטודנט לא יכול לאשר בקשה"""
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
        """בדיקה שסטודנט יכול ליצור בקשה עם קובץ מצורף"""
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
        """בדיקה שצוות יכול לצפות בהתראות שלו"""
        Notification.objects.create(user=self.staff, message='התראה חדשה')
        self.client.login(username='staff_operations', password='password123')
        response = self.client.get(reverse('all_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'התראה חדשה')

    def test_profile_edit_access(self):
        """בדיקה שסטודנט יכול לגשת לעריכת פרופיל"""
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_picture_upload(self):
        """בדיקה שסטודנט יכול לעדכן תמונת פרופיל"""
        self.client.login(username='student_for_staff', password='password123')
        image = SimpleUploadedFile("avatar.jpg", b"testcontent", content_type="image/jpeg")
        response = self.client.post(reverse('profile'), {
            'profile_pic': image
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.profile_pic.name.startswith('profile_pics/'))

    def test_request_filter_by_status(self):
        """בדיקה של סינון בקשות לפי סטטוס"""
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
        self.assertContains(response, 'מאושר') 

    def test_request_filter_by_priority(self):
        """בדיקה של סינון לפי עדיפות"""
        Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='בדיקה לפי עדיפות',
            course=self.course,
            priority=3  
        )
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('list_requests') + '?priority=גבוהה')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'גבוהה')


    def test_request_filter_by_date_range(self):
        """בדיקה של סינון בקשות לפי טווח תאריכים"""
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
        """בדיקה שסטודנט לא יכול לצפות בבקשות של סטודנט אחר"""
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

    def test_notification_toggle_status(self):
        """בדיקה של החלפת סטטוס התראה"""
        notif = Notification.objects.create(user=self.staff, message='בדיקת סטטוס')
        self.client.login(username='staff_operations', password='password123')
        response = self.client.post(
        reverse('toggle_notification_status'),
        data=json.dumps({'notification_id': notif.id, 'read': True}),
        content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.read)


    def test_add_course_missing_name(self):
        """בדיקה שניסיון להוסיף קורס ללא שם נכשל"""
        self.client.login(username='staff_operations', password='password123')

        response = self.client.post(reverse('add_course'), {
            'name': '',
            'year': 'שנה_לא_מספר'  
        }, follow=True)

        self.assertFalse(Course.objects.filter(name='').exists())

        messages = list(response.context['messages'])
        found_error = any("שנת הלימוד חייבת להיות מספר" in str(m) for m in messages)
        self.assertTrue(found_error)

    def test_dashboard_access(self):
        """בדיקה שסטודנט יכול לגשת לדשבורד"""
        self.client.login(username='student_for_staff', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_request_detail_page(self):
        """בדיקה שעמוד פרטי בקשה נפתח תקין"""
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
        self.client.login(username='staff_extra', password='password123')
        response = self.client.get(reverse('export_requests_csv'))
        self.assertEqual(response.status_code, 200)

    def test_export_dashboard_excel(self):
        self.client.login(username='staff_extra', password='password123')
        response = self.client.get(reverse('export_dashboard_excel'))
        self.assertEqual(response.status_code, 200)

    def test_add_course_invalid_year(self):
        self.client.login(username='staff_extra', password='password123')
        response = self.client.post(reverse('add_course'), {
            'name': 'ללא שנה תקינה',
            'year': 'abc'
        }, follow=True)
        self.assertFalse(Course.objects.filter(name='ללא שנה תקינה').exists())

    def test_edit_profile_invalid_picture_type(self):
        self.client.login(username='student_extra', password='password123')
        bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")
        response = self.client.post(reverse('profile'), {
            'profile_pic': bad_file
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    
    def test_assign_lecturer_to_course(self):
        self.client.login(username='staff_extra', password='password123')
        lecturer = User.objects.create_user(
            username='lect1',
            password='pass',
            email='lect1@test.com',
            department=self.department,
            role=1,
            is_active=True,
            first_name="מרצה",
            last_name="בדיקה"
        )
        response = self.client.post(reverse('assign_lecturers_to_course', args=[self.course.id]), {
            'lecturers': [lecturer.id]
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(lecturer, self.course.user_set.all())

    def test_assign_student_to_course(self):
        self.client.login(username='staff_extra', password='password123')
        new_student = User.objects.create_user(
            username='s2', password='pass', department=self.department, role=0, is_active=True
        )
        response = self.client.post(reverse('assign_students_to_course', args=[self.course.id]), {
            'students': [new_student.id]
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(new_student, self.course.user_set.all())


    def test_request_detail_permission_denied(self):
        other_student = User.objects.create_user(
            username='unauthorized_student',
            password='12345678',
            department=self.department,
            role=0,
            is_active=True
        )
        request = Request.objects.create(
            student=other_student,
            dept=self.department,
            title=0,
            description='פרטי בקשה',
            course=self.course
        )
        self.client.login(username='student_extra', password='password123')
        response = self.client.get(reverse('request_detail', args=[request.id]))
        self.assertIn(response.status_code, [302, 403])

    def test_staff_sees_only_their_department_requests(self):
        other_department = Department.objects.create(name='מחלקה אחרת')
        other_course = Course.objects.create(name='קורס אחר', year=1, dept=other_department)
        other_student = User.objects.create_user(
            username='external_student',
            password='pass',
            department=other_department,
            role=0,
            is_active=True
        )
        Request.objects.create(
            student=other_student,
            dept=other_department,
            title=0,
            description='בקשה ממחלקה אחרת',
            course=other_course
        )

        self.client.login(username='staff_operations', password='password123')
        response = self.client.get(reverse('list_requests'))
        self.assertNotContains(response, 'בקשה ממחלקה אחרת')

    
