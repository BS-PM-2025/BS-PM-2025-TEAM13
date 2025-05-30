from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

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
    lecturers = models.ManyToManyField('User', related_name='taught_courses', limit_choices_to={'role': 1}, blank=True)

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
        (0, 'ממתין'),
        (1, 'אושר'),
        (2, 'נדחה')
    )

    PIPELINE_STATUSES = (
        (0, 'נשלח'),
        (1, 'בבדיקה'),
        (2, 'בטיפול'),
        (3, 'בהמתנה למסמכים נוספים'),
        (4, 'טופל - אושר'),
        (5, 'טופל - נדחה'),
        (6, 'בהמתנה')
    )

    PRIORITY_LEVELS = (
        (0, 'נמוכה'),
        (1, 'בינונית'),
        (2, 'גבוהה'),
        (3, 'דחופה')
    )

    TITLES = (
        (0, 'הגשת אישורים'),
        (1, 'בקשה למועד מיוחד'),
        (2, 'שקלול עבודות בית בציון הסופי'),
        (3, 'דחיית הגשת עבודה'),
        (4, 'שחרור מחובת הרשמה'),
        (5, 'בקשה לפטור מקורס'),
        (6, 'ערעור על ציון'),
        (7, 'בקשה לפטור מעבודת הגשה'),
        (8, 'בקשה לפטור מדרישת קדם'),
        (9, 'בקשה לעזרה מיוחדת - דיקאנט'),
        (10, 'אחר')
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 0},related_name='submitted_requests')
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    title = models.SmallIntegerField(default=10, choices=TITLES)
    description = models.TextField()
    status = models.SmallIntegerField(default=0, choices=STATUSES)
    pipeline_status = models.SmallIntegerField(default=0, choices=PIPELINE_STATUSES)
    priority = models.SmallIntegerField(default=1, choices=PRIORITY_LEVELS)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    assigned_to = models.ManyToManyField(User, related_name='assigned_requests',limit_choices_to={'role__in': [1, 2, 3]},
                                         blank=True)
    viewers = models.ManyToManyField(User, related_name='viewable_requests', blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    attachments = models.FileField(upload_to='request_attachments/', null=True, blank=True)

    def update_status(self, pipeline_status, user, notes=''):
        self.pipeline_status = pipeline_status
        if pipeline_status in [4, 5]:
            self.status = 1 if pipeline_status == 4 else 2  # 1=Approved, 2=Rejected
            self.resolved_date = timezone.now()
        else:
            self.status = 0  # Pending

        self.save()
        RequestStatus.objects.create(request=self,status=pipeline_status,updated_by=user,notes=notes)
        notification_type = 'updated'
        if pipeline_status == 3:  # Pending Additional Information
            notification_type = 'info_requested'
        elif pipeline_status in [4, 5]:  # Resolved
            notification_type = 'resolved'

        #send_request_notification(self, notification_type)

    def get_current_status_display(self):
        return dict(self.PIPELINE_STATUSES)[self.pipeline_status]

    def get_remaining_days_display(self):
        if self.status != 0:
            return "טופל"

        from django.utils import timezone
        sla_days_map = {
            0: 7,
            1: 3,
            2: 2,
            3: 1,
        }

        allowed_days = sla_days_map.get(self.priority, 2)
        deadline = self.created + timedelta(days=allowed_days)
        remaining_days = (deadline - timezone.now()).days

        if remaining_days >= 3:
            return f"{remaining_days} ימים"
        elif remaining_days == 2:
            return "יומיים"
        elif remaining_days == 1:
            return "יום"
        elif remaining_days == 0:
            return "היום האחרון"
        else:
            overdue = abs(remaining_days)
            if overdue == 1:
                return '<span class="text-danger">באיחור של יום</span>'
            elif overdue == 2:
                return '<span class="text-danger">באיחור של יומיים</span>'
            else:
                return f'<span class="text-danger">באיחור של {overdue} ימים</span>'



    def get_sla_status(self):
        if self.status != 0:  # If not pending, SLA doesn't apply
            return "Resolved"

        # Get elapsed time
        from django.utils import timezone
        elapsed = (timezone.now() - self.created).total_seconds() / 3600

        # Define SLA thresholds based on priority (in hours)
        sla_thresholds = {
            0: 168,  # Low: 7 days
            1: 72,  # Medium: 3 days
            2: 48,  # High: 2 day
            3: 24,  # Urgent: 1 hours
        }

        threshold = sla_thresholds.get(self.priority, 48)

        if elapsed > threshold:
            return "בחריגה"
        elif elapsed > (threshold * 0.75):
            return "בסיכון"
        else:
            return "בזמן"


    def auto_assign(self):
        self.viewers.clear()
        if not self.pk:
            self.save()
        self.assigned_to.clear()
        staff_users = User.objects.filter(role=2, department=self.dept)  # Staff
        self.viewers.add(*staff_users)

        assigned_users = []
        for user in staff_users:
            assigned_users.append(user)
            self.assigned_to.add(user)

        title_num = self.title

        if title_num in [0, 9]:  # Deanery
            deanery_users = User.objects.filter(role=3)
            if deanery_users.exists():
                for deanery_user in deanery_users:
                    self.assigned_to.add(deanery_user)
                    assigned_users.append(deanery_user)
                self.viewers.add(*deanery_users)
                print(f"Assigned to deanery: {list(deanery_users)}")

        elif title_num in [3, 6, 7] and self.course:  # Lecturer
            lecturer_users = User.objects.filter(role=1,department=self.dept,courses=self.course)
            if lecturer_users.exists():
                for lecturer in lecturer_users:
                    self.assigned_to.add(lecturer)
                    assigned_users.append(lecturer)
                self.viewers.add(*lecturer_users)
                print(f"Assigned to lecturers: {list(lecturer_users)}")

        if not assigned_users:
            print("No suitable assignee found")

        return assigned_users

class RequestComment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'Website'
        verbose_name = 'Request Comment'
        verbose_name_plural = 'Request Comments'
        ordering = ['created']  # Chronological order


class RequestStatus(models.Model):
    STATUS_CHOICES = (
        (0, 'נשלח'),
        (1, 'בבדיקה'),
        (2, 'בטיפול'),
        (3, 'בהמתנה למסמכים נוספים'),
        (4, 'טופל - אושר'),
        (5, 'טופל - נדחה'),
        (6, 'בהמתנה')
    )

    request = models.ForeignKey('Request', on_delete=models.CASCADE, related_name='status_updates')
    status = models.SmallIntegerField(choices=STATUS_CHOICES)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'Website'
        verbose_name = 'Request Status Update'
        verbose_name_plural = 'Request Status Updates'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_status_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}{'...' if len(self.message) > 30 else ''}"

"""
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.rating}"


"""
class Review(models.Model):
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="משתמש",
        related_name='reviews'
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="דירוג",
        help_text="דירוג מ-1 עד 5 כוכבים"
    )

    message = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        verbose_name="הודעה",
        help_text="הודעה אופציונלית מהמשתמש"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="תאריך יצירה"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="תאריך עדכון"
    )

    is_hidden = models.BooleanField(
        default=False,
        verbose_name="מוסתר",
        help_text="האם הביקורת מוסתרת מהציבור"
    )

    class Meta:
        verbose_name = "ביקורת"
        verbose_name_plural = "ביקורות"
        ordering = ['-created_at']

        # Ensure one review per user
        unique_together = ['user']

        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_hidden']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rating} כוכבים"

    def get_star_display(self):
        return "★" * self.rating + "☆" * (5 - self.rating)

    def is_positive(self):
        return self.rating >= 4

    def is_negative(self):
        return self.rating <= 2

    @classmethod
    def get_average_rating(cls):
        from django.db.models import Avg
        result = cls.objects.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'] or 0, 2)

    @classmethod
    def get_rating_distribution(cls):
        from django.db.models import Count
        distribution = {}
        for i in range(1, 6):
            distribution[i] = cls.objects.filter(rating=i).count()
        return distribution

    @classmethod
    def get_satisfaction_rate(cls):
        total = cls.objects.count()
        if total == 0:
            return 0

        satisfied = cls.objects.filter(rating__gte=4).count()
        return round((satisfied / total) * 100, 1)
    
