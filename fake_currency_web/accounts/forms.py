from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'profile_pic']