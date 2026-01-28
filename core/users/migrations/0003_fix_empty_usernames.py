from django.db import migrations
from django.db.models import Q


def fix_empty_usernames(apps, schema_editor):
    """Fix users with empty or NULL usernames by setting them to email"""
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Find all users with empty or NULL usernames
    empty_username_users = CustomUser.objects.filter(
        Q(username='') | Q(username__isnull=True)
    )
    
    print(f"Found {empty_username_users.count()} users with empty usernames")
    
    for user in empty_username_users:
        if user.email:
            # Set username to email
            user.username = user.email
            user.save(update_fields=['username'])
            print(f"  Fixed: {user.email}")
        else:
            # If no email either, set a placeholder
            user.username = f"user_{user.id}"
            user.save(update_fields=['username'])
            print(f"  Fixed with placeholder: user_{user.id}")


def reverse_fix_empty_usernames(apps, schema_editor):
    """Reverse migration (no-op)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_school_options_school_academic_calendar_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_empty_usernames, reverse_fix_empty_usernames),
    ]
