import random
import string
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
import uuid
from django.contrib.auth import get_user_model


class UserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_email_verified = models.BooleanField(default=False)  # Track if email is verified

    def __str__(self):
        return f"{self.user.username} Profile"

class OpenSpace(models.Model):
    DISTRICT_CHOICES = [
        ('Kinondoni', 'Kinondoni'),
        ('Ilala', 'Ilala'),
        ('Ubungo', 'Ubungo'),
        ('Temeke', 'Temeke'),
        ('Kigamboni', 'Kigamboni'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
    ]
    
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
class ReportHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    report_id = models.CharField(max_length=8, editable=False)
    description = models.TextField()
    email = models.EmailField(blank=True, null=True)
    file = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    

class Report(models.Model):
    report_id = models.CharField(max_length=8, unique=True, editable=False)
    description = models.TextField()
    email = models.EmailField(blank=True, null=True)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    space_name = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    def save(self, *args, **kwargs):
        # Generate unique ID if not already set
        is_new = not self.pk
        if not self.report_id:
            self.report_id = self._generate_unique_id()
        super().save(*args, **kwargs)
        # Send email notification if email is provided and it's a new report
        if is_new and self.email:
            self._send_notification_email()

    def _generate_unique_id(self):
        # Generate a unique 8-character ID
        unique_id = uuid.uuid4().hex[:8].upper()
        # Check if ID already exists, if so, generate a new one
        while Report.objects.filter(report_id=unique_id).exists():
            unique_id = uuid.uuid4().hex[:8].upper()
        return unique_id
    
    def _send_notification_email(self):
        subject = f'Report Received - ID: {self.report_id}'
        
        message = f'''
    ------------------------------------------------------------
    Kinondoni Environmental Report Acknowledgement
    ------------------------------------------------------------

    Your report has been successfully received.

    Report ID: {self.report_id}  
    Submission Date: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
    Location: {self.space_name if self.space_name else "Not specified"}

    Thank you for taking the time to report an environmental issue.  
    Our team will review your report and take the appropriate action as soon as possible.

    Please use the Report ID above to track the progress of your report.

    ------------------------------------------------------------
    This is an automated message. Please do not reply.  
    If you need assistance, please visit our help center.

    Thank you for supporting a cleaner and safer environment.  
    Kinondoni Environmental Team
    ------------------------------------------------------------
        '''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )


class ReportReply(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="replies")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.report.report_id} by {self.sender}"
