from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
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
        
        # יצירת מזכירות
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
