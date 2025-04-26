from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class Department(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'Website'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    year = models.SmallIntegerField(default=1)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'Website'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

class User(AbstractUser):
    email = models.EmailField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    info = models.CharField(max_length=100) ## 'Reservist, Extension'
    profile_pic = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True,
        default="images/profile.png"
    )

    roles = (
        (0, 'Student'),
        (1, 'Lecturer'),
        (2, 'Staff'),
        (3, 'Deanery'))
    role = models.SmallIntegerField(default=0, choices=roles)
    courses = models.ManyToManyField("Course", blank=True)
    year = models.SmallIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.role == 1 and self._state.adding:
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta:
        app_label = 'Website'
        db_table = 'Website_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    groups = models.ManyToManyField(
        Group,
        related_name='website_user_set',
        blank=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='website_user_permissions_set',
        blank=True
    )

class Request(models.Model):
    STATUSES = (
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected')
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE,limit_choices_to={'role': 0})
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    description = models.TextField()
    status = models.SmallIntegerField(default=0, choices=STATUSES)
    created = models.DateTimeField(auto_now_add=True)
    # sla field - function to calc

    class Meta:
        app_label = 'Website'
        verbose_name = 'Request'
        verbose_name_plural = 'Requests'

