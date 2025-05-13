from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from .models import User
from .forms import RegistrationForm
from django.shortcuts import render
from django.http import JsonResponse
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
            if not user.profile_pic:
                user.profile_pic = 'images/profile.png'
            user.save()
            return redirect("/Website/login")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {"form": form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/Website/home")
    return render(request, 'login.html')

def login_request(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect("/Website/home")
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html', {'form': AuthenticationForm()})

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/Website/login")

class Registration(CreateView):
    model = User
    form_class = RegistrationForm
    template_name = 'register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/Website/home/')


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            user.profile_pic = request.FILES['profile_pic']
            user.save()
            messages.success(request, "Profile picture updated successfully!")

        if 'old_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully!")
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})


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
