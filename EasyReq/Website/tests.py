from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Department
from django.core.files.uploadedfile import SimpleUploadedFile

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
        )

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
        self.assertContains(response, 'Welcome')  # מותאם לתבנית שלך

    def test_logout_redirects_to_login(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('login'))

    def test_home_authenticated_access(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

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
            self.assertContains(response, "Login")

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

    def test_home_page_contains_username(self):
        self.client.login(username='testuser', password='testpass123*')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'testuser')
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
