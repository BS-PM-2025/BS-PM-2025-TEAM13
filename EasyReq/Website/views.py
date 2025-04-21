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
