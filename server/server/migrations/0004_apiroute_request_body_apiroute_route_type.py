# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0003_emailverification'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiroute',
            name='request_body',
            field=models.JSONField(blank=True, help_text='Expected request body for validation', null=True),
        ),
        migrations.AddField(
            model_name='apiroute',
            name='route_type',
            field=models.CharField(choices=[('STANDARD', 'Standard Response'), ('EMAIL_OTP', 'Email OTP Verification')], default='STANDARD', max_length=20),
        ),
    ]
