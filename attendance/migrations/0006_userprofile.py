from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_profiles(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])
    Profile = apps.get_model('attendance', 'UserProfile')
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_session_session_end_time_session_session_start_time_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='users/avatars/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.RunPython(create_profiles, migrations.RunPython.noop),
    ]

