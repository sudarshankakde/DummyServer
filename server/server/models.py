from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
import secrets
from django.utils import timezone
from datetime import timedelta


def route_upload_to(instance, filename: str) -> str:
    owner = instance.project.owner.username if instance.project and instance.project.owner else "anon"
    project = instance.project.slug if instance.project and instance.project.slug else "project"
    return f"routes/{owner}/{project}/{filename}"


class EmailVerification(models.Model):
    """Model to store email verification tokens"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verification")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Verification for {self.user.email}"


class EmailOTP(models.Model):
    """Model to store email OTP for verification"""
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    route = models.ForeignKey('ApiRoute', on_delete=models.CASCADE, related_name='otps')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp}"


class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("owner", "slug"),)

    def __str__(self) -> str:
        return f"{self.owner}:{self.slug}"


class ApiRoute(models.Model):
    class HttpMethod(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"
        HEAD = "HEAD", "HEAD"
        OPTIONS = "OPTIONS", "OPTIONS"
    
    class RouteType(models.TextChoices):
        STANDARD = "STANDARD", "Standard Response"
        EMAIL_OTP = "EMAIL_OTP", "Email OTP Verification"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="routes")
    method = models.CharField(max_length=10, choices=HttpMethod.choices, default=HttpMethod.GET)
    path = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(regex=r"^/", message="Path must start with a '/'."),
            RegexValidator(regex=r"^\S+$", message="Path cannot contain whitespace."),
        ],
        help_text="Route path within the project, e.g. /users/list",
    )
    route_type = models.CharField(max_length=20, choices=RouteType.choices, default=RouteType.STANDARD)
    status_code = models.PositiveSmallIntegerField(default=200)
    content_type = models.CharField(max_length=120, default="application/json")
    request_body = models.JSONField(null=True, blank=True, help_text="Expected request body for validation")
    response_json = models.JSONField(null=True, blank=True)
    response_file = models.FileField(upload_to=route_upload_to, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("project", "method", "path"),)

    def clean(self):
        super().clean()
        if self.response_file and not str(self.response_file.name).lower().endswith(".json"):
            raise ValidationError({"response_file": "Only .json files are allowed."})
        
        # For EMAIL_OTP routes, response is auto-generated
        if self.route_type == self.RouteType.EMAIL_OTP:
            return
        
        has_json = self.response_json is not None
        has_file = bool(self.response_file)
        
        # Response is required unless route type is EMAIL_OTP
        if not has_json and not has_file:
            raise ValidationError(
                {"response_json": "Provide either inline JSON or upload a JSON file for standard routes."}
            )
        
        # Can't have both
        if has_json and has_file:
            raise ValidationError(
                {"response_json": "Provide either inline JSON or upload a JSON file, not both."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.project} {self.method} {self.path}"
