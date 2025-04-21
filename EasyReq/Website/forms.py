from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django import forms
from .models import User, Department

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    role = forms.ChoiceField(choices=User.roles)
    email = forms.EmailField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    profile_pic = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'password1', 'password2',
                  'first_name', 'last_name', 'role',
                  'email', 'department', 'profile_pic']

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data.get('role')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.department = self.cleaned_data.get('department')

        profile_pic = self.cleaned_data.get('profile_pic')
        if profile_pic:
            user.profile_pic = profile_pic
        else:
            user.profile_pic = 'images/profile.png'

        if commit:
            user.save()
        return user
