import json
import os
import base64
from datetime import datetime, timedelta

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user_model
)

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from django.http import HttpResponse

from django.db.models import Count
from django.utils import timezone

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

import openpyxl

from .models import DetectionHistory, Payment, Subscription

# ✅ CNN IMPORT
from .cnn_predict import predict_currency

User = get_user_model()

FREE_DETECTION_LIMIT = 15
PLAN_PRICE_PER_MONTH = 99
PLAN_MONTHS = [1, 2, 3, 6]


def get_subscription_context(user):
    subscription = (
        Subscription.objects
        .filter(user=user, is_active=True, expires_at__gte=timezone.now())
        .first()
    )

    detection_count = DetectionHistory.objects.filter(user=user).count()
    remaining_free = max(FREE_DETECTION_LIMIT - detection_count, 0)

    plans = [
        {
            "months": months,
            "amount": months * PLAN_PRICE_PER_MONTH,
            "label": f"{months} Month" if months == 1 else f"{months} Months",
        }
        for months in PLAN_MONTHS
    ]

    return {
        "subscription": subscription,
        "has_subscription": subscription is not None,
        "detection_count": detection_count,
        "free_detection_limit": FREE_DETECTION_LIMIT,
        "remaining_free": remaining_free,
        "plans": plans,
    }


# =========================================================
# REGISTER VIEW
# =========================================================
def register_view(request):

    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, "register.html")


# =========================================================
# LOGIN VIEW
# =========================================================
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            # ADMIN LOGIN
            if role == "admin":

                if user.is_staff or user.is_superuser:
                    return redirect("admin_dashboard")

                else:
                    messages.error(request, "You are not an Admin!")
                    return redirect("login")

            # USER LOGIN
            elif role == "user":
                return redirect("dashboard")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


# =========================================================
# DASHBOARD
# =========================================================
@login_required(login_url='login')
def dashboard_view(request):
    return render(
        request,
        "dashboard.html",
        get_subscription_context(request.user)
    )


@login_required(login_url='login')
def subscribe_view(request, months):
    if months not in PLAN_MONTHS:
        messages.error(request, "Invalid subscription plan.")
        return redirect("dashboard")

    amount = months * PLAN_PRICE_PER_MONTH

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "").upper()
        upi_id = request.POST.get("upi_id", "").strip()

        if payment_method not in ["UPI", "CARD", "NETBANKING"]:
            messages.error(request, "Please select a payment method.")
            return redirect("subscribe", months=months)

        if payment_method == "UPI" and "@" not in upi_id:
            messages.error(request, "Please enter a valid UPI ID, for example name@upi.")
            return redirect("subscribe", months=months)

        payment = Payment.objects.create(
            user=request.user,
            plan_months=months,
            amount=amount,
            payment_method=payment_method,
            upi_id=upi_id,
            status="PENDING",
        )

        return redirect("payment_processing", payment_id=payment.id)

    return render(
        request,
        "payment.html",
        {
            "months": months,
            "amount": amount,
            "label": f"{months} Month" if months == 1 else f"{months} Months",
        }
    )


@login_required(login_url='login')
def payment_processing_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    return render(
        request,
        "payment_processing.html",
        {"payment": payment}
    )


@login_required(login_url='login')
def payment_success_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.status != "SUCCESS":
        payment.status = "SUCCESS"
        payment.save(update_fields=["status"])

        now = timezone.now()
        expires_at = now + timedelta(days=30 * payment.plan_months)

        Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                "plan_months": payment.plan_months,
                "amount": payment.amount,
                "expires_at": expires_at,
                "is_active": True,
            }
        )

    subscription = Subscription.objects.get(user=request.user)

    return render(
        request,
        "payment_success.html",
        {
            "payment": payment,
            "subscription": subscription,
        }
    )


# =========================================================
# LOGOUT
# =========================================================
def logout_view(request):

    logout(request)

    messages.success(request, "Logged out successfully!")

    return redirect('login')


# =========================================================
# DETECTOR VIEW
# =========================================================
@login_required(login_url="login")
def detector_view(request):

    context = {}
    subscription_context = get_subscription_context(request.user)

    if (
        not subscription_context["has_subscription"]
        and subscription_context["remaining_free"] <= 0
    ):
        messages.error(
            request,
            "Your 15 free detections are finished. Please buy a subscription."
        )
        return redirect("dashboard")

    # ======================================
    # IMAGE UPLOAD DETECTION
    # ======================================
    if request.method == "POST" and request.FILES.get("note_image"):

        image = request.FILES["note_image"]

        fs = FileSystemStorage()

        filename = fs.save(image.name, image)

        file_url = fs.url(filename)

        # IMAGE FULL PATH
        full_path = os.path.join(
            settings.MEDIA_ROOT,
            filename
        )

        # ✅ CNN PREDICTION
        prediction = predict_currency(full_path)

        result = prediction["result"]

        confidence = prediction["confidence"]

        country = prediction["country"]

        currency_name = prediction["currency_name"]

        currency_value = prediction["currency_value"]

        serial_number = prediction["serial_number"]

        prediction_text = (
            f"{result} "
            f"({confidence}% confidence)"
        )

        # SAVE DATABASE
        DetectionHistory.objects.create(
            user=request.user,
            image=filename,
            result=result,
            confidence=confidence
        )

        context = {
            "file_url": file_url,
            "prediction": prediction_text,
            "country": country,
            "currency_name": currency_name,
            "currency_value": currency_value,
            "serial_number": serial_number
        }
        context.update(get_subscription_context(request.user))

    # ======================================
    # CAMERA DETECTION
    # ======================================
    elif request.method == "POST" and request.POST.get("camera_image"):

        format, imgstr = request.POST.get(
            "camera_image"
        ).split(';base64,')

        ext = format.split('/')[-1]

        file = ContentFile(
            base64.b64decode(imgstr),
            name='captured.' + ext
        )

        fs = FileSystemStorage()

        filename = fs.save(file.name, file)

        file_url = fs.url(filename)

        # IMAGE FULL PATH
        full_path = os.path.join(
            settings.MEDIA_ROOT,
            filename
        )

        # ✅ CNN PREDICTION
        prediction = predict_currency(full_path)

        result = prediction["result"]

        confidence = prediction["confidence"]

        country = prediction["country"]

        currency_name = prediction["currency_name"]

        currency_value = prediction["currency_value"]

        serial_number = prediction["serial_number"]

        prediction_text = (
            f"{result} "
            f"({confidence}% confidence)"
        )

        # SAVE DATABASE
        DetectionHistory.objects.create(
            user=request.user,
            image=filename,
            result=result,
            confidence=confidence
        )

        context = {
            "file_url": file_url,
            "prediction": prediction_text,
            "country": country,
            "currency_name": currency_name,
            "currency_value": currency_value,
            "serial_number": serial_number
        }
        context.update(get_subscription_context(request.user))

    return render(request, "detector.html", context)


# =========================================================
# HISTORY
# =========================================================
@login_required
def history(request):

    filter_type = request.GET.get("filter")

    sort = request.GET.get("sort")

    records = DetectionHistory.objects.filter(user=request.user)

    # FILTER
    if filter_type == "Real":
        records = records.filter(result="Real")

    elif filter_type == "Fake":
        records = records.filter(result="Fake")

    # SORT
    if sort == "old":
        records = records.order_by("created_at")

    else:
        records = records.order_by("-created_at")

    return render(
        request,
        "history.html",
        {"records": records}
    )


# =========================================================
# DELETE SINGLE RECORD
# =========================================================
@login_required
@require_POST
def delete_record(request, id):

    record = get_object_or_404(
        DetectionHistory,
        id=id,
        user=request.user,
    )

    record.delete()

    return redirect("history")


# =========================================================
# DELETE ALL HISTORY
# =========================================================
@login_required
@require_POST
def delete_all_history(request):

    DetectionHistory.objects.filter(user=request.user).delete()

    return redirect("history")


# =========================================================
# PIE CHART
# =========================================================
def generate_pie_chart(real, fake):

    drawing = Drawing(300, 200)

    pie = Pie()

    pie.x = 100
    pie.y = 50
    pie.width = 120
    pie.height = 120

    pie.data = [real, fake]

    pie.labels = ["Real", "Fake"]

    pie.slices.strokeWidth = 0.5

    pie.slices[0].fillColor = HexColor("#4CAF50")

    pie.slices[1].fillColor = HexColor("#F44336")

    drawing.add(pie)

    return drawing


# =========================================================
# EXPORT PDF
# =========================================================
@login_required
def export_pdf(request):

    filename = (
        f"currency_report_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response)

    elements = []

    styles = getSampleStyleSheet()

    title = Paragraph(
        "Fake Currency Detection Report",
        styles["Title"]
    )

    elements.append(title)

    elements.append(Spacer(1, 12))

    records = DetectionHistory.objects.filter(user=request.user)

    total = records.count()

    real = records.filter(result="Real").count()

    fake = records.filter(result="Fake").count()

    chart = generate_pie_chart(real, fake)

    elements.append(chart)

    elements.append(Spacer(1, 20))

    data = [[
        "Image",
        "Result",
        "Confidence",
        "Date"
    ]]

    for r in records:

        try:
            img_path = r.image.path

        except:
            img_path = None

        if img_path and os.path.exists(img_path):

            img = Image(
                img_path,
                0.7 * inch,
                0.7 * inch
            )

        else:
            img = "No Image"

        data.append([
            img,
            r.result,
            f"{r.confidence}%",
            r.created_at.strftime("%d-%m-%Y %H:%M")
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.darkgreen),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

        ("FONTSIZE", (0,0), (-1,-1), 8),

        ("ALIGN", (0,0), (-1,-1), "CENTER")

    ]))

    elements.append(table)

    doc.build(elements)

    return response


# =========================================================
# EXPORT EXCEL
# =========================================================
@login_required
def export_excel(request):

    wb = openpyxl.Workbook()

    ws = wb.active

    ws.title = "History Report"

    ws.append([
        "ID",
        "Result",
        "Confidence",
        "Date"
    ])

    for r in DetectionHistory.objects.filter(user=request.user):

        ws.append([
            r.id,
            r.result,
            f"{r.confidence}%",
            r.created_at.strftime("%d-%m-%Y %H:%M")
        ])

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    filename = (
        f"history_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{filename}"'

    wb.save(response)

    return response


# =========================================================
# PROFILE
# =========================================================
@login_required
def profile_view(request):

    return render(
        request,
        "profile.html",
        {"user": request.user}
    )


# =========================================================
# EDIT PROFILE
# =========================================================
@login_required
def edit_profile(request):

    user = request.user

    if request.method == "POST":

        user.username = request.POST.get("username")

        user.email = request.POST.get("email")

        user.first_name = request.POST.get("first_name")

        user.last_name = request.POST.get("last_name")

        user.save()

        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect('accounts:profile')

    return render(
        request,
        "edit_profile.html",
        {"user": user}
    )


# =========================================================
# USER DASHBOARD
# =========================================================
@login_required
def user_dashboard(request):

    return render(
        request,
        "dashboard.html",
        get_subscription_context(request.user)
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================
@staff_member_required
def admin_dashboard(request):

    result_colors = {
        "Fake": "#ff4d4d",
        "Real": "#00e676",
        "Error": "#ff9800",
        "Uncertain": "#ffd600",
    }

    result_data = (
        DetectionHistory.objects
        .values('result')
        .annotate(total=Count('id'))
        .order_by('result')
    )

    labels = [
        item['result']
        for item in result_data
    ]

    values = [
        item['total']
        for item in result_data
    ]

    colors = [
        result_colors.get(label, "#64b5f6")
        for label in labels
    ]

    # LAST 30 DAYS
    last_30_days = timezone.now() - timedelta(days=30)

    daily_data = (
        DetectionHistory.objects
        .filter(created_at__gte=last_30_days)
        .extra(select={'day': "date(created_at)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    days = [
        str(item['day'])
        for item in daily_data
    ]

    counts = [
        item['count']
        for item in daily_data
    ]

    return render(
        request,
        "admin_dashboard.html",
        {
            "labels": json.dumps(labels),
            "values": json.dumps(values),
            "colors": json.dumps(colors),
            "days": json.dumps(days),
            "counts": json.dumps(counts),
        }
    )
