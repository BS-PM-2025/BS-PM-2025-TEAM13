from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django import forms
from pkg_resources import require

from .models import User, Department


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name =  forms.CharField(required=True)
    role = forms.ChoiceField(choices=User.roles)
    email = forms.CharField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data.get('role')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.department = self.cleaned_data.get('department')
        if commit:
            user.save()
        return user

