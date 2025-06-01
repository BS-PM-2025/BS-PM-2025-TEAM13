from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from .models import User, Course, Request, RequestStatus, RequestComment, Department
from .forms import RegistrationForm
from django.shortcuts import render
from django.http import JsonResponse
from django.db import models
from django.core.paginator import Paginator
from .utils import send_request_notification
from django.utils import timezone
import csv
import openpyxl
from openpyxl.styles import Font, Alignment
import io
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render
from .models import Notification

def home(request):
    return render(request, 'home.html', {'user': request.user})

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            if user.role == 1:
                user.is_active = 0
                selected_courses = request.POST.getlist('courses')
                if selected_courses:
                    for course_id in selected_courses:
                        user.courses.add(course_id)
            if user.role == 0:
                relevant_courses = Course.objects.filter(year=user.year, dept=user.department)
                if relevant_courses.exists():
                    user.courses.add(*relevant_courses)
            return redirect('registration_success', user_id=user.id)
    else:
        form = RegistrationForm()

    departments = Department.objects.all()
    courses = Course.objects.all()
    return render(request, 'register.html', {"form": form, "departments": departments, "courses": courses})

def registration_success(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        role = user.role
        context = {'user': user, 'role': role}
        return render(request, 'registration_success.html', context)
    except User.DoesNotExist:
        return redirect('register')


def get_courses(request):
    department_id = request.GET.get('department')
    if not department_id:
        return JsonResponse({'courses': []})
    courses = Course.objects.filter(dept=department_id).values('id', 'name')
    return JsonResponse({'courses': list(courses)})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/Website/home")
    return render(request, 'login.html')

def login_request(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username = form.data.get('username')
        try:
            user_obj = User.objects.get(username=username)
            if not user_obj.is_active:
                messages.error(request, "המשתמש שלך ממתין לאישור מנהל מערכת")
                return HttpResponseRedirect("/login")
        except User.DoesNotExist:
            pass

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect("")
            else:
                messages.error(request, "שגיאה באחד מפרטי הזיהוי")
        else:
            messages.error(request, "שגיאה באחד מפרטי הזיהוי")

    return render(request, 'login.html', {'form': AuthenticationForm()})

@login_required
def logout_view(request):
    logout(request)
    return redirect("home")

class Registration(CreateView):
    model = User
    form_class = RegistrationForm
    template_name = 'register.html'

    def form_valid(self, form):
        user = form.save()
        path_ = "/registration-success/" + str(user.id)
        return redirect(path_, user_id=user.id)

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            user.profile_pic = request.FILES['profile_pic']
            user.save()
            messages.success(request, "!תמונת הפרופיל עודכנה בהצלחה")

        if 'old_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "!הסיסמה עודכנה בהצלחה")
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})

def create_request(request):
    if request.method == 'POST':
        student = request.user
        dept_id = student.department_id
        course_id = request.POST.get('course')
        title_id = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 1)
        attachment = request.FILES.get('attachment')
        new_request = Request(student=student,dept_id=dept_id,title=int(title_id),description=description,
                              priority=priority,attachments=attachment)

        if course_id:
            new_request.course_id = course_id

        new_request.save()
        assigned_users = new_request.auto_assign()
        RequestStatus.objects.create(request=new_request,status=0, updated_by=request.user,notes="Request submitted")

        if len(assigned_users) > 0:
            send_request_notification(new_request, 'created')
            for user in assigned_users:
                send_request_notification(new_request, 'assigned', user)

        return redirect('request_detail', request_id=new_request.id)

    departments = Department.objects.all()
    courses = request.user.courses.all() if request.user.role == 0 else []

    # Get available templates
   # if request.user.role == 0:  # Only students see templates
   #     templates = RequestTemplate.objects.filter(
   #         dept=request.user.department,
   #         is_active=True
   #     )
   # else:
    #    templates = []

    return render(request, 'create_request.html', {'departments': departments,'courses': courses,
                'title_choices': Request.TITLES,})
    #'templates': templates
def request_detail(request, request_id):
    req = Request.objects.get(pk=request_id)
    assigned_users = list(req.assigned_to.all())
    print(f"Request #{req.id} is assigned to: {assigned_users}")
    has_access = (request.user == req.student or req.assigned_to.filter(id=request.user.id).exists() or
            request.user.role in [2, 3] or  req.viewers.filter(id=request.user.id).exists())

    if not has_access:
        messages.error(request, "אין לך הרשאות לצפות בבקשה זו.")
        return redirect('list_requests')

    if request.method == 'POST':
        comment = request.POST.get('comment')
        if comment:
            RequestComment.objects.create(request=req,user=request.user,comment=comment)
            if request.user == req.student:
                for assigned_user in req.assigned_to.all():
                    send_request_notification(req, 'comment', assigned_user)
                    print(f"Sent comment notification to assigned user: {assigned_user}")
            else:
                send_request_notification(req, 'comment', req.student)
                print(f"Sent comment notification to student: {req.student}")

        return redirect('request_detail', request_id=req.id)

    comments = req.comments.all()
    return render(request, 'request_detail.html', {'request': req,'comments': comments,'sla_status': req.get_sla_status()})


def update_request_status(request, request_id):
    PIPELINE_STATUSES = (
        (0, 'נשלח'),
        (1, 'בבדיקה'),
        (2, 'בטיפול'),
        (3, 'בהמתנה למסמכים נוספים'),
        (4, 'טופל - אושר'),
        (5, 'טופל - נדחה'),
        (6, 'בהמתנה')
    )

    if not request.user.role in [1, 2, 3]:  # staff
        return redirect('home')

    req = Request.objects.get(pk=request_id)

    if request.method == 'POST':
        new_pipeline_status = int(request.POST.get('pipeline_status'))
        status_notes = request.POST.get('status_notes', '')
        resolution_notes = request.POST.get('resolution_notes', '')
        req.pipeline_status = new_pipeline_status
        if new_pipeline_status in [4, 5]:  # Resolved
            # 4=approved, 5=rejected
            req.status = 1 if new_pipeline_status == 4 else 2
            req.resolution_notes = resolution_notes
            req.resolved_date = timezone.now()
        else:
            req.status = 0

        req.save()
        RequestStatus.objects.create(request=req,status=new_pipeline_status,updated_by=request.user,notes=status_notes)
        pipeline_status_text = dict(PIPELINE_STATUSES)[new_pipeline_status]
        RequestComment.objects.create(request=req,user=request.user,
            comment=f"סטטוס עודכן ל: {pipeline_status_text}\n\n{status_notes}")

        notification_type = None

        if new_pipeline_status in [4, 5]:
            notification_type = 'resolved'
        elif new_pipeline_status == 3:
            notification_type = 'info_requested'
        else:
            notification_type = 'updated'

        if 'notify_student' in request.POST:
            send_request_notification(req, notification_type)
            if notification_type == 'resolved' and req.assigned_to.exists():
                for assigned_user in req.assigned_to.all():
                    send_request_notification(req, 'resolved', assigned_user)

        return redirect('request_detail', request_id=req.id)

    return render(request, 'update_request.html', {'request': req,'statuses': PIPELINE_STATUSES})


@require_http_methods(["GET", "POST"])
@login_required
def list_requests(request):
    user = request.user

    if request.method == "POST" and "delete_request_id" in request.POST:
        request_id = request.POST.get("delete_request_id")
        req_to_delete = get_object_or_404(Request, id=request_id)

        if user == req_to_delete.student or user.role in [1, 2, 3]:
            req_to_delete.delete()
            messages.success(request, "הבקשה נמחקה בהצלחה.")
            return redirect('list_requests')
        else:
            messages.error(request, "אין לך הרשאה למחוק בקשה זו.")
            return redirect('list_requests')

    if user.role == 0:
        base_queryset = Request.objects.filter(student=user)
    elif user.role in [1, 2, 3]:
        base_queryset = Request.objects.filter(
            models.Q(viewers=user) | models.Q(assigned_to=user)
        ).distinct()
    else:
        base_queryset = Request.objects.none()

    search_query = request.GET.get('q')
    if search_query:
        base_queryset = base_queryset.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(resolution_notes__icontains=search_query)
        )

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

    request_title = request.GET.get('request_title')
    if request_title and request_title.isdigit():
        base_queryset = base_queryset.filter(title=int(request_title))

    date_range = request.GET.get('date_range')
    if date_range:
        from datetime import datetime, timedelta
        today = timezone.now().date()
        
        if date_range == 'today':
            base_queryset = base_queryset.filter(created__date=today)
        elif date_range == 'yesterday':
            yesterday = today - timedelta(days=1)
            base_queryset = base_queryset.filter(created__date=yesterday)
        elif date_range == 'this_week':
            start_week = today - timedelta(days=today.weekday())
            base_queryset = base_queryset.filter(created__date__gte=start_week)
        elif date_range == 'last_week':
            start_week = today - timedelta(days=today.weekday() + 7)
            end_week = today - timedelta(days=today.weekday() + 1)
            base_queryset = base_queryset.filter(created__date__range=[start_week, end_week])
        elif date_range == 'this_month':
            start_month = today.replace(day=1)
            base_queryset = base_queryset.filter(created__date__gte=start_month)
        elif date_range == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            base_queryset = base_queryset.filter(created__date__range=[first_day_last_month, last_day_last_month])
        elif date_range == 'this_year':
            start_year = today.replace(month=1, day=1)
            base_queryset = base_queryset.filter(created__date__gte=start_year)

    sla = request.GET.get('sla')
    if sla:
        pending = base_queryset.filter(status=0)
        if sla == 'overdue':
            overdue_ids = [req.id for req in pending if req.get_sla_status() == "בחריגה"]
            base_queryset = base_queryset.filter(id__in=overdue_ids)
        elif sla == 'at_risk':
            at_risk_ids = [req.id for req in pending if req.get_sla_status() == "בסיכון"]
            base_queryset = base_queryset.filter(id__in=at_risk_ids)
        elif sla == 'on_track':
            on_track_ids = [req.id for req in pending if req.get_sla_status() == "בזמן"]
            base_queryset = base_queryset.filter(id__in=on_track_ids)

    from datetime import datetime
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            base_queryset = base_queryset.filter(created__gte=date_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59)
            base_queryset = base_queryset.filter(created__lte=date_to)
        except ValueError:
            pass

    base_queryset = base_queryset.order_by('-created')

    paginator = Paginator(base_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    status_counts = [
        base_queryset.filter(status=0).count(),  
        base_queryset.filter(status=1).count(),  
        base_queryset.filter(status=2).count(),
    ]

    departments = Department.objects.all()

    if user.role == 0:  # Student
        user_request_titles = Request.objects.filter(student=user).values_list('title', flat=True).distinct()
        user_request_titles = [(title, dict(Request.TITLES)[title]) for title in user_request_titles]
    elif user.role in [1, 2, 3]:  # Staff/Lecturers
        user_request_titles = Request.objects.filter(
            models.Q(viewers=user) | models.Q(assigned_to=user)
        ).values_list('title', flat=True).distinct()
        user_request_titles = [(title, dict(Request.TITLES)[title]) for title in user_request_titles]
    else:
        user_request_titles = []

    context = {
        'page_obj': page_obj,
        'departments': departments,
        'statuses': Request.STATUSES,
        'pipeline_statuses': Request.PIPELINE_STATUSES,
        'priorities': Request.PRIORITY_LEVELS,
        'user_request_titles': user_request_titles, 
        'search_query': search_query,
        'filters': {
            'status': request.GET.get('status'),
            'pipeline_status': request.GET.get('pipeline_status'),
            'priority': request.GET.get('priority'),
            'department': request.GET.get('department'),
            'request_title': request.GET.get('request_title'),  
            'date_range': request.GET.get('date_range'),  
            'date_from': request.GET.get('date_from'),
            'date_to': request.GET.get('date_to'),
            'sla': request.GET.get('sla'),
        },
        'status_counts': status_counts,  
    }

    return render(request, 'list_requests.html', context)

def get_filtered_requests(request):
    user = request.user
    if user.role == 0:  # Student
        base_queryset = Request.objects.filter(student=user)
    elif user.role in [1, 2, 3]:  # Lecturer, Staff, Deanery
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

    # newest first
    return base_queryset.order_by('-created')

def base(request):
    loginuser = request.user
    return render(request, 'base.html', {'role': loginuser.role})

def approve_lecturer(request):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        try:
            lecturer = User.objects.get(id=user_id, role=1)
            if action == 'approve':
                lecturer.is_active = True
                lecturer.save()
                messages.success(request, f"המרצה {lecturer.get_full_name()} אושר בהצלחה.")
                send_lecturer_approval_email(lecturer, approved=True)

            elif action == 'reject':
                send_lecturer_approval_email(lecturer, approved=False)
                lecturer.delete() #change?
                messages.success(request, f"בקשת המרצה {lecturer.get_full_name()} נדחתה.")

        except User.DoesNotExist:
            messages.error(request, "המשתמש לא נמצא.")

    return redirect('department_dashboard')


def add_course(request):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    department = request.user.department
    if not department:
        messages.error(request, "לא משוייך למחלקה. אנא פנה למנהל המערכת.")
        return redirect('home')

    lecturers = User.objects.filter(role=1, is_active=True, department=department)
    if request.method == 'POST':
        name = request.POST.get('name')
        lecturer_ids = request.POST.getlist('lecturers')
        year = request.POST.get('year')
        course = Course.objects.create(name=name,dept_id=department.id,year=int(year))
        if lecturer_ids:
            lecturers_to_assign = User.objects.filter(id__in=lecturer_ids)
            for lecturer in lecturers_to_assign:
                lecturer.courses.add(course)

        messages.success(request, f"הקורס {name} נוסף בהצלחה למערכת.")
        return redirect('department_dashboard')
    return render(request, 'add_course.html', {'lecturers': lecturers})

def student_requests(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לצפות בדף זה.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.role == 1 and request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לצפות בבקשות של סטודנט זה.")
        return redirect('department_dashboard')

    requests = Request.objects.filter(student=student).order_by('-created')
    return render(request, 'student_requests.html', {'student': student,'requests': requests})

def send_lecturer_approval_email(lecturer, approved=True):
    subject = "EasyReq - אישור חשבון מרצה" if approved else "EasyReq - דחיית בקשת רישום"
    context = {'lecturer': lecturer,'approved': approved,'login_url': settings.BASE_URL + '/login/'
    if hasattr(settings, 'BASE_URL') else 'http://localhost:8000/login/'}

    html_message = render_to_string('lecturer_approval_email.html', context)
    plain_message = "חשבונך במערכת EasyReq אושר. ניתן להתחבר באמצעות הקישור." if approved else "בקשת הרישום שלך למערכת EasyReq נדחתה."

    try:
        send_mail(subject,plain_message,settings.DEFAULT_FROM_EMAIL,[lecturer.email],html_message=html_message,
                  fail_silently=False)
        print(f"Approval email sent to lecturer {lecturer.email}")
    except Exception as e:
        print(f"Failed to send approval email: {e}")


def edit_student(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לערוך פרטים של סטודנט זה.")
        return redirect('department_dashboard')

    if request.method == 'POST':
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.email = request.POST.get('email')
        student.info = request.POST.get('info')
        student.is_active = 'is_active' in request.POST
        student.save()
        messages.success(request, f"פרטי הסטודנט {student.get_full_name()} עודכנו בהצלחה.")

    return redirect('student_requests', student_id=student_id)


def assign_student_courses(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לערוך פרטים של סטודנט זה.")
        return redirect('department_dashboard')

    if request.method == 'POST':
        course_ids = request.POST.getlist('courses')
        student.courses.clear()
        if course_ids:
            courses = Course.objects.filter(id__in=course_ids, dept=student.department)
            student.courses.add(*courses)

        messages.success(request, f"הקורסים של הסטודנט {student.get_full_name()} עודכנו בהצלחה.")

    return redirect('student_requests', student_id=student_id)

def deactivate_student(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו על סטודנט זה.")
        return redirect('department_dashboard')

    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f"חשבון הסטודנט {student.get_full_name()} הושבת בהצלחה.")

    return redirect('department_dashboard')


def edit_student_form(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    # Check department access
    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לערוך פרטים של סטודנט זה.")
        return redirect('department_dashboard')

    if request.method == 'POST':
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.email = request.POST.get('email')
        student.info = request.POST.get('info')
        student.is_active = 'is_active' in request.POST
        student.save()
        messages.success(request, f"פרטי הסטודנט {student.get_full_name()} עודכנו בהצלחה.")
        return redirect('department_dashboard')

    context = {'student': student,}
    return render(request, 'edit_student.html', context)


def assign_student_courses_form(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לערוך פרטים של סטודנט זה.")
        return redirect('department_dashboard')

    department_courses = Course.objects.filter(dept=student.department)

    if request.method == 'POST':
        course_ids = request.POST.getlist('courses')
        student.courses.clear()
        if course_ids:
            courses = Course.objects.filter(id__in=course_ids, dept=student.department)
            student.courses.add(*courses)

        messages.success(request, f"הקורסים של הסטודנט {student.get_full_name()} עודכנו בהצלחה.")
        return redirect('department_dashboard')

    context = {'student': student,'courses': department_courses,'assigned_courses': student.courses.all(),}
    return render(request, 'assign_student_courses.html', context)


def confirm_deactivate_student(request, student_id):
    if not request.user.is_authenticated or request.user.role != 2:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו על סטודנט זה.")
        return redirect('department_dashboard')

    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f"חשבון הסטודנט {student.get_full_name()} הושבת בהצלחה.")
        return redirect('department_dashboard')

    context = {'student': student,}
    return render(request, 'confirm_deactivate_student.html', context)


def activate_student(request, student_id):
    if not request.user.is_authenticated or request.user.role not in [2, 3]:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו.")
        return redirect('home')

    try:
        student = User.objects.get(id=student_id, role=0)
    except User.DoesNotExist:
        messages.error(request, "הסטודנט לא נמצא.")
        return redirect('department_dashboard')

    if request.user.department != student.department:
        messages.error(request, "אין לך הרשאות לבצע פעולה זו על סטודנט זה.")
        return redirect('department_dashboard')

    student.is_active = True
    student.save()
    messages.success(request, f"חשבון הסטודנט {student.get_full_name()} הופעל בהצלחה.")
    return redirect('department_dashboard')
  
@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    try:
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def all_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'all_notifications.html', {
        'notifications': notifications
    })

@login_required
@require_http_methods(["POST"])
def toggle_notification_status(request):
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        read_status = data.get('read') 
        
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.read = read_status
        notification.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def export_requests_csv(request):
    filtered_requests = get_filtered_requests(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Requests_export.xlsx"'
    writer = csv.writer(response)
    writer.writerow([
        'מס׳ בקשה', 'סוג בקשה', 'סטודנט', 'מחלקה', 'קורס', 'סטטוס',
        'שלב בתהליך', 'דחיפות', 'תאריך יצירה', 'תאריך טיפול', 'מטפלים'
    ])

    for req in filtered_requests:
        assigned_users = ", ".join([user.get_full_name() for user in req.assigned_to.all()])
        course_name = req.course.name if req.course else ""
        resolved_date = req.resolved_date.strftime('%d/%m/%Y %H:%M') if req.resolved_date else ""
        writer.writerow([
            req.id,
            req.get_title_display(),
            req.student.get_full_name(),
            req.dept.name,
            course_name,
            req.get_status_display(),
            req.get_current_status_display(),
            req.get_priority_display(),
            req.created.strftime('%d/%m/%Y %H:%M'),
            resolved_date,
            assigned_users
        ])

    return response

def export_requests_excel(request):
    filtered_requests = get_filtered_requests(request)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requests"

    # Define headers
    headers = [
        'מס׳ בקשה', 'סוג בקשה', 'סטודנט', 'מחלקה', 'קורס', 'סטטוס',
        'שלב בתהליך', 'דחיפות', 'תאריך יצירה', 'תאריך טיפול', 'הערות', 'מטפלים'
    ]

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Write data rows
    row_num = 2
    for req in filtered_requests:
        assigned_users = ", ".join([user.get_full_name() for user in req.assigned_to.all()])
        course_name = req.course.name if req.course else ""
        resolved_date = req.resolved_date.strftime('%d/%m/%Y %H:%M') if req.resolved_date else ""

        row = [
            req.id,
            req.get_title_display(),
            req.student.get_full_name(),
            req.dept.name,
            course_name,
            req.get_status_display(),
            req.get_current_status_display(),
            req.get_priority_display(),
            req.created.strftime('%d/%m/%Y %H:%M'),
            resolved_date,
            req.resolution_notes[:250] if req.resolution_notes else "",
            assigned_users
        ]

        for col_num, cell_value in enumerate(row, 1):
            ws.cell(row=row_num, column=col_num, value=cell_value)

        row_num += 1

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                cell_length = len(str(cell.value))
                if cell_length > max_length:
                    max_length = cell_length
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = 'attachment; filename="Requests_export.xlsx"'

    return response
