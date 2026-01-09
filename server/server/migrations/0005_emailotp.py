# Generated migration for EmailOTP model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0004_apiroute_request_body_apiroute_route_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('verified', models.BooleanField(default=False)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to='server.apiroute')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
