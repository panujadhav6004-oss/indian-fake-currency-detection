from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ProfileForm, RegisterForm
from .models import Profile

User = get_user_model()


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if role == "admin":
                if user.is_staff or user.is_admin:
                    return redirect("admin_dashboard")

                messages.error(request, "You are not an Admin!")
                return redirect("login")

            return redirect("dashboard")

        messages.error(request, "Invalid Username or Password")

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please login.")
            return redirect("login")

        messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            return redirect("accounts:profile_view")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/profile.html", {"profile": profile, "form": form})


@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            return redirect("accounts:profile_view")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form})