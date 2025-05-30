from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django import forms
from .models import User, Department
from django.core.exceptions import ValidationError
import re
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    role = forms.ChoiceField(choices=User.roles)
    email = forms.EmailField(required=True)
    year = forms.ChoiceField(choices=[
        (0, 'מרצה'),
        (1, 'שנה א'),
        (2, 'שנה ב'),
        (3, 'שנה ג'),
        (4, 'שנה ד')
    ], required=False, initial=0)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    profile_pic = forms.ImageField(required=False)
    def clean_email(self):
        email = self.cleaned_data['email']
        pattern = r'^[\w\.-]+@(ac\.sce\.ac\.il|sce\.ac\.il)$'

        if not re.match(pattern, email):
            raise ValidationError("עליך להזין מייל מכללתי בלבד")

        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        year = cleaned_data.get('year')

        if role == 0 and not year:
            raise forms.ValidationError("עליך להזין שנת לימוד")

        return cleaned_data
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'password1', 'password2',
                  'first_name', 'last_name', 'role',
                  'email', 'department', 'profile_pic', 'year']

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = int(self.cleaned_data.get('role'))
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.department = self.cleaned_data.get('department')
        if self.cleaned_data.get('year') == '':
            user.year = 0
        else:
            user.year = int(self.cleaned_data.get('year'))

        profile_pic = self.cleaned_data.get('profile_pic')
        if profile_pic:
            user.profile_pic = profile_pic
        else:
            user.profile_pic = 'images/profile.png'

        if commit:
            user.save()
        return user

