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
    """סימון התראה בודדת כנקראה"""
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
    """סימון כל ההתראות כנקראות"""
    try:
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def all_notifications(request):
    """צפייה בכל ההתראות כולל אלו שנקראו"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'all_notifications.html', {
        'notifications': notifications
    })

@login_required
@require_http_methods(["POST"])
def toggle_notification_status(request):
    """החלפת סטטוס התראה בין נקרא ללא נקרא"""
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

