from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from .models import User, Course
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
            user.save()
            if user.role == 1:
                user.is_active = 0
            if user.role == 0:
                relevant_courses = Course.objects.filter(year=user.year, dept=user.department)
                if relevant_courses.exists():
                    user.courses.add(*relevant_courses)
            return redirect('registration_success', user_id=user.id)
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {"form": form})

def registration_success(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        role = user.role
        context = {'user': user, 'role': role}
        return render(request, 'registration_success.html', context)
    except User.DoesNotExist:
        return redirect('register')

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



