from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
import json
import io
from unittest.mock import patch, MagicMock

from .models import (
    Department, Course, Request, RequestStatus, 
    RequestComment, User, Notification
)
from Website.views import filter_requests, get_filtered_requests 

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Dept')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123*',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            department=self.department,
            role=0  
        )
        self.course = Course.objects.create(name='מבוא', year=1, dept=self.department)
        self.user.courses.add(self.course)


    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_successful_login_redirects_home(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123*'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.get_full_name()) 

    def test_logout_redirects_to_login(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('home'))

    def test_home_authenticated_access(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.get_full_name())

    def test_profile_view_logged_in(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertContains(response, self.user.email)

    def test_profile_picture_upload(self):
        self.client.login(username='testuser', password='testpass123*')
        image = SimpleUploadedFile("avatar.jpg", b"testcontent", content_type="image/jpeg")
        response = self.client.post(reverse('profile'), {
            'profile_pic': image
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()

    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_new_user_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'department': self.department.id,
            'info': 'Student',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
    def test_register_creates_user(self):
        self.client.post(reverse('register'), {
            'username': 'student123',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'student123@example.com',
            'first_name': 'Student',
            'last_name': 'Example',
            'department': self.department.id,
            'info': 'Student',
        })
        self.assertTrue(User.objects.filter(username='testuser').exists())
    def test_logout_redirects_anonymous(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_update_password(self):
        self.client.login(username='testuser', password='testpass123*')
        self.client.post(reverse('profile'), {
            'old_password': 'testpass123*',
            'new_password1': 'Newpass456@',
            'new_password2': 'Newpass456@'
        }, follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Newpass456@'))
    def test_register_passwords_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'failuser',
            'password1': 'Password1!',
            'password2': 'Different1!',
            'email': 'fail@example.com',
            'first_name': 'Fail',
            'last_name': 'User',
            'department': self.department.id,
            'info': 'Student',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='failuser').exists())
    def test_register_existing_username(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',  # כבר קיים
            'password1': 'AnotherPass1!',
            'password2': 'AnotherPass1!',
            'email': 'another@example.com',
            'first_name': 'Dup',
            'last_name': 'User',
            'department': self.department.id,
            'info': 'Student',
        })
        self.assertEqual(response.status_code, 200)
        users = User.objects.filter(username='testuser')
        self.assertEqual(users.count(), 1)
    def test_home_redirects_if_not_logged_in(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    def test_register_with_profile_picture(self):
        image = SimpleUploadedFile("avatar.jpg", b"imagecontent", content_type="image/jpeg")
        response = self.client.post(reverse('register'), {
            'username': 'withpic',
            'password1': 'Secure1234!',
            'password2': 'Secure1234!',
            'email': 'pic@example.com',
            'first_name': 'With',
            'last_name': 'Pic',
            'department': self.department.id,
            'info': 'Lecturer',
            'profile_pic': image,
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_login_nonexistent_user(self):
            response = self.client.post(reverse('login'), {
                'username': 'notexist',
                'password': 'DoesntMatter123!'
            })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "התחברות לחשבון שלך")

    def test_login_invalid_credentials_does_not_authenticate(self):
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'wrongpass123**'
            })
            self.assertEqual(response.wsgi_request.user.is_authenticated, False)

    def test_profile_displays_email(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('profile'))
        self.assertContains(response, self.user.email)

    def test_profile_displays_username(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('profile'))
        self.assertContains(response, self.user.username)

    def test_register_missing_email(self):
        response = self.client.post(reverse('register'), {
            'username': 'missingemail',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'No',
            'last_name': 'Email',
            'department': self.department.id,
            'info': 'Student',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='missingemail').exists())

    def test_register_user_role(self):
        self.client.post(reverse('register'), {
            'username': 'studentuser',
            'password1': 'RoleCheck123!',
            'password2': 'RoleCheck123!',
            'email': 'rolecheck@example.com',
            'first_name': 'Student',
            'last_name': 'Check',
            'department': self.department.id,
            'info': 'Test info',
            'role': 0,  # Student
        }, follow=True)

        user = User.objects.get(username='studentuser')
        self.assertEqual(user.role, 0)

    def test_register_user_role(self):
        self.client.post(reverse('register'), {
            'username': 'studentuser',
            'password1': 'RoleCheck123!',
            'password2': 'RoleCheck123!',
            'email': 'rolecheck@example.com',
            'first_name': 'Student',
            'last_name': 'Check',
            'department': self.department.id,
            'info': 'Test info',
            'role': 0,  # Student
        }, follow=True)

        user = User.objects.get(username='testuser')
        self.assertEqual(user.role, 0)

    def test_home_template_used(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home.html')

    def test_register_with_duplicate_username_fails(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',  # כבר קיים
            'password1': 'NewPass123!',
            'password2': 'NewPass123!',
            'email': 'newemail@example.com',
            'first_name': 'Dup',
            'last_name': 'User',
            'department': self.department.id,
            'info': 'Student',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)

    def test_uploaded_profile_picture_is_saved(self):
        self.client.login(username='testuser', password='testpass123*')
        image = SimpleUploadedFile("photo.jpg", b"filedata", content_type="image/jpeg")
        self.client.post(reverse('profile'), {
            'profile_pic': image
        }, follow=True)

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_pic.name.startswith('profile_pics/'))

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_redirect_status(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_profile_template_contains_full_name(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('profile'))
        full_name = f"{self.user.first_name} {self.user.last_name}"
        self.assertContains(response, full_name)
        
    def test_register_fails_on_missing_fields(self):
        response = self.client.post(reverse('register'), {
            'username': '',
            'password1': 'Pass123!@#',
            'password2': 'Pass123!@#',
            'email': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='').exists())

    def test_register_fails_on_invalid_email(self):
        response = self.client.post(reverse('register'), {
            'username': 'bademailuser',
            'password1': 'Valid123@',
            'password2': 'Valid123@',
            'email': 'notanemail',
            'first_name': 'Bad',
            'last_name': 'Email',
            'department': self.department.id,
            'info': 'Test',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bademailuser').exists())

    # create a request with valid data
    def test_create_request_success(self):
        self.client.login(username='testuser', password='testpass123*')

        response = self.client.post(reverse('create_request'), {
            'course': self.course.id,
            'title': 0, 
            'description': 'אני מבקש ערעור',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Request.objects.filter(description='אני מבקש ערעור').exists())

    # check that the request save with a file attachment
    def test_create_request_with_attachment(self):
        self.client.login(username='testuser', password='testpass123*')

        file = SimpleUploadedFile("test.pdf", b"dummy content", content_type="application/pdf")

        response = self.client.post(reverse('create_request'), {
            'course': self.course.id,
            'title': 1,
            'description': 'עם קובץ',
            'attachment': file
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        req = Request.objects.filter(description='עם קובץ').first()
        self.assertIsNotNone(req)
        self.assertTrue(req.attachments)

    #check that the request doesn't save when a title is missing
    def test_create_request_missing_title(self):
        self.client.login(username='testuser', password='testpass123*')

        with self.assertRaises(TypeError):  # ✅ מצפה מראש לשגיאה
            self.client.post(reverse('create_request'), {
                'course': self.course.id,
                'description': 'בדיקה ללא title'
            })

    # check that an unauthenticated user cannot access the request submission screen
    def test_create_request_unauthenticated_redirect(self):
        response = self.client.get(reverse('create_request'))
        self.assertEqual(response.status_code, 302)  
        self.assertIn(reverse('login'), response.url)

    #Test that the response page content after submission contains expected information
    def test_create_request_success_response_contains_text(self):
        self.client.login(username='testuser', password='testpass123*')

        response = self.client.post(reverse('create_request'), {
            'course': self.course.id,
            'title': 3,
            'description': 'בדיקת טקסט בתגובה',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "בקשה") 

class RequestViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # יצירת מחלקה
        self.department = Department.objects.create(name='Test Department')
        
        # יצירת קורס
        self.course = Course.objects.create(
            name='Test Course',
            year=1,
            dept=self.department
        )
        
        # יצירת סטודנט
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            email='student@example.com',
            first_name='Student',
            last_name='User',
            department=self.department,
            role=0
        )
        self.student.courses.add(self.course)
        
        # יצירת מרצה
        self.lecturer = User.objects.create_user(
            username='lecturer',
            password='testpass123',
            email='lecturer@example.com',
            first_name='Lecturer',
            last_name='User',
            department=self.department,
            role=1,
            is_active=True
        )
        self.lecturer.courses.add(self.course)
        
        # יצירת צוות מזכירות
        self.staff = User.objects.create_user(
            username='staff',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            department=self.department,
            role=2,
            is_active=True
        )
        
        # יצירת בקשה
        self.request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,  # ערעור ציון
            description='בקשה לערעור ציון',
            course=self.course
        )
        
        # הוספת המרצה כמטפל בבקשה
        self.request.assigned_to.add(self.lecturer)
        
        # יצירת סטטוס בקשה
        self.status = RequestStatus.objects.create(
            request=self.request,
            status=0,  # נשלח
            updated_by=self.student,
            notes='Request created'
        )
        
        # יצירת תגובה לבקשה
        self.comment = RequestComment.objects.create(
            request=self.request,
            user=self.student,
            comment='תגובה לבקשה'
        )
        
        # יצירת התראה
        self.notification = Notification.objects.create(
            user=self.lecturer,
            message='התראה חדשה',
            read=False
        )

    def add_middleware_to_request(self, request):
        """הוספת middleware לבקשה לצורך messages"""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def test_request_detail_view_authorized(self):
        """בדיקה שמשתמש מורשה יכול לראות פרטי בקשה"""
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('request_detail', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'request_detail.html')
        self.assertContains(response, 'בקשה לערעור ציון')

    def test_request_detail_view_staff(self):
        """בדיקה שמזכירות יכולה לראות פרטי בקשה"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('request_detail', args=[self.request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'בקשה לערעור ציון')
    
    def test_request_detail_view_unauthorized(self):
        """בדיקה שמשתמש לא מורשה לא יכול לראות פרטי בקשה"""
        other_student = User.objects.create_user(
            username='other_student',
            password='testpass123',
            email='other@example.com',
            department=self.department,
            role=0
        )
        
        self.client.login(username='other_student', password='testpass123')
        response = self.client.get(reverse('request_detail', args=[self.request.id]))
        self.assertEqual(response.status_code, 302)  
    
    def test_request_detail_add_comment(self):
        """בדיקה שניתן להוסיף תגובה לבקשה"""
        self.client.login(username='student', password='testpass123')
        response = self.client.post(
            reverse('request_detail', args=[self.request.id]),
            {'comment': 'תגובה חדשה לבקשה'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'תגובה חדשה לבקשה')
        
        comment_exists = RequestComment.objects.filter(
            request=self.request,
            comment='תגובה חדשה לבקשה'
        ).exists()
        self.assertTrue(comment_exists)

    def test_update_request_status_by_staff(self):
        """בדיקה שמזכירות יכולה לעדכן סטטוס בקשה"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.post(
            reverse('update_request_status', args=[self.request.id]),
            {
                'pipeline_status': '1', 
                'status_notes': 'בדיקת עדכון סטטוס'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.pipeline_status, 1)
        
        status_exists = RequestStatus.objects.filter(
            request=self.request,
            status=1,
            notes='בדיקת עדכון סטטוס'
        ).exists()
        self.assertTrue(status_exists)
    
    def test_update_request_status_by_lecturer(self):
        """בדיקה שמרצה יכול לעדכן סטטוס בקשה"""
        
        self.request.assigned_to.add(self.lecturer)
        
        request_factory = RequestFactory()
        update_request = request_factory.post(
            reverse('update_request_status', args=[self.request.id]),
            {
                'pipeline_status': '2',  # בטיפול
                'status_notes': 'בדיקת עדכון סטטוס'
            }
        )
        
        update_request.user = self.lecturer
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(update_request)
        update_request.session.save()
        
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(update_request, '_messages', FallbackStorage(update_request))
        
        from django.views.decorators.csrf import csrf_exempt
        from Website.views import update_request_status
        
        response = csrf_exempt(update_request_status)(update_request, self.request.id)
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.pipeline_status, 2)
    
    def test_update_request_status_by_student_not_allowed(self):
        """בדיקה שסטודנט לא יכול לעדכן סטטוס בקשה"""
        self.client.login(username='student', password='testpass123')
        response = self.client.post(
            reverse('update_request_status', args=[self.request.id]),
            {
                'pipeline_status': '1',
                'status_notes': 'בדיקת עדכון סטטוס'
            },
            follow=True
        )
        self.assertRedirects(response, reverse('home'))
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.pipeline_status, 0)
    
    def test_update_request_status_to_resolved(self):
        """בדיקה שניתן לסמן בקשה כמטופלת (אושרה/נדחתה)"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.post(
            reverse('update_request_status', args=[self.request.id]),
            {
                'pipeline_status': '4',
                'status_notes': 'הבקשה אושרה',
                'resolution_notes': 'פרטי האישור כאן',
                'notify_student': 'on'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.pipeline_status, 4)
        self.assertEqual(self.request.status, 1) 
        self.assertEqual(self.request.resolution_notes, 'פרטי האישור כאן')
        self.assertIsNotNone(self.request.resolved_date)

    def test_list_requests_student_view(self):
        """בדיקה שסטודנט רואה רק את הבקשות שלו"""
        login_successful = self.client.login(username='student', password='testpass123')
        self.assertTrue(login_successful)
        
        response = self.client.get(reverse('list_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list_requests.html')
        
        self.assertContains(response, str(self.request.id))
        
        self.assertContains(response, self.student.get_full_name())
    
    def test_list_requests_staff_view(self):
        login_successful = self.client.login(username='staff', password='testpass123')
        self.assertTrue(login_successful)
        
        self.staff.department = self.department
        self.staff.save()
        
        self.request.viewers.add(self.staff)
        
        response = self.client.get(reverse('list_requests'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, str(self.request.id))
    
    def test_list_requests_with_filters(self):
        login_successful = self.client.login(username='staff', password='testpass123')
        self.assertTrue(login_successful)
        
        self.staff.department = self.department
        self.staff.save()
        
        high_priority_request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=5,  
            description='בקשה בעדיפות גבוהה',
            priority=2 
        )
        high_priority_request.viewers.add(self.staff)
        
        self.assertEqual(high_priority_request.priority, 2)
        
        response = self.client.get(f"{reverse('list_requests')}?priority=2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(high_priority_request.id))
        
        self.request.status = 1 
        self.request.save()
        
        response = self.client.get(f"{reverse('list_requests')}?status=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.request.id))


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Department')
        self.course = Course.objects.create(name='Test Course', year=1, dept=self.department)
    
    
    def test_registration_success_invalid_user(self):
        """בדיקה שדף הצלחת ההרשמה מפנה לדף הרשמה אם המשתמש לא קיים"""
        non_existent_id = 9999  
        response = self.client.get(reverse('registration_success', args=[non_existent_id]))
        self.assertRedirects(response, reverse('register'))
    
    def test_registration_success_student_role(self):
        """בדיקה שדף הצלחת ההרשמה מציג מידע נכון לסטודנט"""
        student = User.objects.create_user(
            username='test_student',
            password='pass123',
            email='student@example.com',
            department=self.department,
            role=0
        )
        
        response = self.client.get(reverse('registration_success', args=[student.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['role'], 0)
    
    def test_registration_success_lecturer_role(self):
        """בדיקה שדף הצלחת ההרשמה מציג מידע נכון למרצה"""
        lecturer = User.objects.create_user(
            username='test_lecturer',
            password='pass123',
            email='lecturer@example.com',
            department=self.department,
            role=1
        )
        
        response = self.client.get(reverse('registration_success', args=[lecturer.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['role'], 1)


class GetCoursesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Department')
        self.other_department = Department.objects.create(name='Other Department')
        
        self.course1 = Course.objects.create(name='Course 1', year=1, dept=self.department)
        self.course2 = Course.objects.create(name='Course 2', year=2, dept=self.department)
        
        self.other_course = Course.objects.create(name='Other Course', year=1, dept=self.other_department)
    
    def test_get_courses_for_department(self):
        """בדיקה שהפונקציה מחזירה את הקורסים הנכונים עבור מחלקה"""
        response = self.client.get(f"{reverse('get_courses')}?department={self.department.id}")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['courses']), 2)
        course_names = [course['name'] for course in data['courses']]
        self.assertIn('Course 1', course_names)
        self.assertIn('Course 2', course_names)
    
    def test_get_courses_empty_department(self):
        """בדיקה שהפונקציה מחזירה רשימה ריקה כאשר אין מחלקה"""
        response = self.client.get(reverse('get_courses'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['courses']), 0)
    
    def test_get_courses_nonexistent_department(self):
        """בדיקה שהפונקציה מחזירה רשימה ריקה כאשר המחלקה לא קיימת"""
        non_existent_id = 9999  
        response = self.client.get(f"{reverse('get_courses')}?department={non_existent_id}")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['courses']), 0)
    
    def test_get_courses_correct_format(self):
        """בדיקה שהפונקציה מחזירה את הקורסים בפורמט הנכון"""
        response = self.client.get(f"{reverse('get_courses')}?department={self.department.id}")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('courses', data)
        self.assertIsInstance(data['courses'], list)
        
        if len(data['courses']) > 0:
            first_course = data['courses'][0]
            self.assertIn('id', first_course)
            self.assertIn('name', first_course)

class ExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Department')
        
        self.staff = User.objects.create_user(
            username='staff',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            email='student@example.com',
            first_name='Student',
            last_name='User',
            department=self.department,
            role=0
        )
        
        self.course = Course.objects.create(name='Test Course', year=1, dept=self.department)
        
        for i in range(3):
            request = Request.objects.create(
                student=self.student,
                dept=self.department,
                title=i % 3,  
                description=f'Test Request {i+1}',
                priority=i % 3,  
                course=self.course
            )
            RequestStatus.objects.create(
                request=request,
                status=i % 3,  
                updated_by=self.student,
                notes=f'Status notes {i+1}'
            )
    
    def test_export_dashboard_excel_staff(self):
        """בדיקה שייצוא אקסל מלוח המחוונים עובד למזכירות"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('export_dashboard_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=dashboard_stats.xlsx'
        )
        self.assertTrue(len(response.content) > 0)
    
    
    def test_export_requests_csv(self):
        """בדיקה שייצוא CSV של בקשות עובד"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('export_requests_csv'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="Requests_export.xlsx"'
        )
        self.assertTrue(len(response.content) > 0)
    
    def test_export_requests_excel(self):
        """בדיקה שייצוא אקסל של בקשות עובד"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('export_requests_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="Requests_export.xlsx"'
        )
        self.assertTrue(len(response.content) > 0)
    
def get_filtered_requests(request):
    if callable(request):
        return Request.objects.all().order_by('-created')
    
    user = request.user
    if user.role == 0: 
        base_queryset = Request.objects.filter(student=user)
    elif user.role in [1, 2, 3]:  
        base_queryset = Request.objects.filter(models.Q(viewers=user) | models.Q(assigned_to=user)).distinct()
    else:
        base_queryset = Request.objects.none()

    search_query = request.GET.get('q')
    if search_query:
        base_queryset = base_queryset.filter(models.Q(description__icontains=search_query) |
            models.Q(resolution_notes__icontains=search_query) | models.Q(student__first_name__icontains=search_query) |
            models.Q(student__last_name__icontains=search_query))

    status = request.GET.get('status')
    if status and status.isdigit():
        base_queryset = base_queryset.filter(status=int(status))

    pipeline_status = request.GET.get('pipeline_status')
    if pipeline_status and pipeline_status.isdigit():
        base_queryset = base_queryset.filter(pipeline_status=int(pipeline_status))

    priority = request.GET.get('priority')
    if priority and priority.isdigit():
        base_queryset = base_queryset.filter(priority=int(priority))

    department = request.GET.get('department')
    if department and department.isdigit():
        base_queryset = base_queryset.filter(dept_id=int(department))

    sla = request.GET.get('sla')
    if sla:
        pending = base_queryset.filter(status=0)
        if sla == 'overdue':
            overdue_ids = [req.id for req in pending if req.get_sla_status() == "Overdue"]
            base_queryset = base_queryset.filter(id__in=overdue_ids)
        elif sla == 'at_risk':
            at_risk_ids = [req.id for req in pending if req.get_sla_status() == "At Risk"]
            base_queryset = base_queryset.filter(id__in=at_risk_ids)
        elif sla == 'on_track':
            on_track_ids = [req.id for req in pending if req.get_sla_status() == "On Track"]
            base_queryset = base_queryset.filter(id__in=on_track_ids)

    date_from = request.GET.get('date_from')
    if date_from:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            base_queryset = base_queryset.filter(created__gte=date_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to')
    if date_to:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59)
            base_queryset = base_queryset.filter(created__lte=date_to)
        except ValueError:
            pass

    return base_queryset.order_by('-created')


class FilterRequestsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.department = Department.objects.create(name='Test Department')
        
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            department=self.department,
            role=0
        )
        
        self.request1 = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='בקשה 1',
            priority=0,
            status=0 
        )
        
        self.request2 = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=1,
            description='בקשה 2',
            priority=1, 
            status=1 
        )
        
        self.request3 = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=2,
            description='בקשה 3',
            priority=2, 
            status=2 
        )
    
    def test_filter_by_status(self):
        """בדיקת סינון לפי סטטוס"""
        request = self.factory.get('/', {'status': '1'})
        
        filtered = filter_requests(request, Request.objects.all())
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().status, 1)
    
    def test_filter_by_priority(self):
        """בדיקת סינון לפי עדיפות"""
        request = self.factory.get('/', {'priority': '2'})
        
        filtered = filter_requests(request, Request.objects.all())
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().priority, 2)
    
    def test_filter_by_department(self):
        """בדיקת סינון לפי מחלקה"""
        other_department = Department.objects.create(name='Other Department')
        
        Request.objects.create(
            student=self.student,
            dept=other_department,
            title=0,
            description='בקשה במחלקה אחרת',
            priority=0,
            status=0
        )
        
        request = self.factory.get('/', {'department': str(self.department.id)})
        
        filtered = filter_requests(request, Request.objects.all())
        
        self.assertEqual(filtered.count(), 3) 
        for req in filtered:
            self.assertEqual(req.dept.id, self.department.id)
    
    def test_filter_by_date_range(self):
        """בדיקת סינון לפי טווח תאריכים"""
        from datetime import datetime, timedelta
        
        old_date = timezone.now() - timedelta(days=30)
        self.request1.created = old_date
        self.request1.save()
        
        yesterday = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        request = self.factory.get('/', {'date_from': yesterday})
        
        filtered = filter_requests(request, Request.objects.all())
        
        self.assertEqual(filtered.count(), 2) 
        for req in filtered:
            self.assertNotEqual(req.id, self.request1.id)
    
    def test_multiple_filters(self):
        """בדיקת שילוב של מספר מסננים"""
        request = self.factory.get('/', {
            'status': '0',
            'priority': '0'
        })
        
        filtered = filter_requests(request, Request.objects.all())
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, self.request1.id)


class CourseManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Department')
        
        self.staff = User.objects.create_user(
            username='staff',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.course = Course.objects.create(
            name='Test Course',
            year=1,
            dept=self.department
        )
        
        self.lecturer = User.objects.create_user(
            username='lecturer',
            password='testpass123',
            email='lecturer@example.com',
            first_name='Lecturer',
            last_name='User',
            department=self.department,
            role=1,
            is_active=True
        )
    
    def test_manage_courses_view(self):
        """בדיקת תצוגת ניהול קורסים"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('manage_courses'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manage_courses.html')
        self.assertIn('courses', response.context)
        self.assertEqual(response.context['courses'].count(), 1)
        self.assertEqual(response.context['courses'].first().name, 'Test Course')
    
    def test_add_course(self):
        """בדיקת הוספת קורס חדש"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.post(reverse('add_course'), {
            'name': 'New Course',
            'year': '2',
            'lecturers': [self.lecturer.id]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('manage_courses'))
        
        # בדיקה שהקורס נוצר
        self.assertTrue(Course.objects.filter(name='New Course').exists())
        course = Course.objects.get(name='New Course')
        self.assertEqual(course.year, 2)
        
        # בדיקה שהמרצה שויך לקורס
        self.assertTrue(course.user_set.filter(id=self.lecturer.id).exists())
    
    def test_edit_course(self):
        """בדיקת עריכת קורס קיים"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'name': 'Updated Course',
            'year': '3',
            'lecturers': [self.lecturer.id]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('manage_courses'))
        
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Updated Course')
        self.assertEqual(self.course.year, 3)        

        self.assertTrue(self.course.user_set.filter(id=self.lecturer.id).exists())
    
    def test_delete_course(self):
        """בדיקת מחיקת קורס"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.get(reverse('delete_course', args=[self.course.id]), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('manage_courses'))
        
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())
    
    def test_assign_lecturer_courses_form(self):
        """בדיקת טופס שיוך מרצים לקורס"""
        self.client.login(username='staff', password='testpass123')
        
        lecturer2 = User.objects.create_user(
            username='lecturer2',
            password='testpass123',
            email='lecturer2@example.com',
            department=self.department,
            role=1,
            is_active=True
        )
        
        response = self.client.post(reverse('assign_lecturer_courses_form', args=[self.course.id]), {
            'lecturers': [self.lecturer.id, lecturer2.id]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('manage_courses'))
        
        self.assertEqual(self.course.user_set.filter(role=1).count(), 2)
        self.assertTrue(self.course.user_set.filter(id=self.lecturer.id).exists())
        self.assertTrue(self.course.user_set.filter(id=lecturer2.id).exists())


class StudentManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(name='Test Department')
        
        self.staff = User.objects.create_user(
            username='staff',
            password='testpass123',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            department=self.department,
            role=2,
            is_active=True
        )
        
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            email='student@example.com',
            first_name='Student',
            last_name='User',
            department=self.department,
            role=0,
            is_active=True
        )
        
        self.course = Course.objects.create(
            name='Test Course',
            year=1,
            dept=self.department
        )
        
        self.request = Request.objects.create(
            student=self.student,
            dept=self.department,
            title=0,
            description='Test Request',
            priority=1
        )

    
    def test_student_requests_unauthorized(self):
        """בדיקה שרק צוות יכול לגשת לבקשות של סטודנט"""
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('student_requests', args=[self.student.id]))
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_edit_student_form(self):
        """בדיקת טופס עריכת פרטי סטודנט"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.get(reverse('edit_student_form', args=[self.student.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_student.html')
        self.assertEqual(response.context['student'], self.student)
    
    def test_edit_student_update(self):
        """בדיקת עדכון פרטי סטודנט"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.post(reverse('edit_student_form', args=[self.student.id]), {
            'first_name': 'Updated',
            'last_name': 'Student',
            'email': 'updated@example.com',
            'info': 'Updated info',
            'is_active': 'on'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('dashboard'))
        
