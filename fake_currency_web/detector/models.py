import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone


class Prediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='notes/')
    result = models.CharField(max_length=20)
    confidence = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class DetectionHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="detections/")
    result = models.CharField(max_length=20)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.result}"


class Subscription(models.Model):
    PLAN_CHOICES = (
        (1, "1 Month"),
        (2, "2 Months"),
        (3, "3 Months"),
        (6, "6 Months"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_months = models.PositiveSmallIntegerField(choices=PLAN_CHOICES)
    amount = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and self.expires_at >= timezone.now()

    def __str__(self):
        return f"{self.user} - {self.plan_months} month(s)"


class Payment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    METHOD_CHOICES = (
        ("UPI", "UPI"),
        ("CARD", "Card"),
        ("NETBANKING", "Net Banking"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_months = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    upi_id = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} - {self.status}"
