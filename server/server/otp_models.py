from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets


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
