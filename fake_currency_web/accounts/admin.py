from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile


# Custom User Admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)


# Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    