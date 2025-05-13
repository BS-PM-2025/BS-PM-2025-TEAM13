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

class Registration(CreateView):
    model = User
    form_class = RegistrationForm
    template_name = 'register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/Website/home/')

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

def create_request(request):
    if request.method == 'POST':
        student = request.user
        dept_id = student.department_id
        course_id = request.POST.get('course')
        title_id = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 1)

        # Optional: handle file upload
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

