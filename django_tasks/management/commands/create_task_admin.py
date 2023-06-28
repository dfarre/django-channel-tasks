import secrets
import string

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission, Group


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('email')

    def handle(self, *args, **options):
        user, created = User.objects.update_or_create(
            {'is_staff': True, 'email': options['email']}, username=options['username'])
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(15))
        user.set_password(password)
        group, _ = Group.objects.get_or_create(name='TaskAdmins')
        group.permissions.add(*Permission.objects.filter(
            content_type__in=ContentType.objects.filter(app_label='django_tasks')))
        group.permissions.add(*Permission.objects.filter(
            content_type__in=ContentType.objects.filter(app_label='authtoken'),
            name='Can add Token'))
        user.groups.add(group)
        user.save()
        self.stdout.write(("Created user " if created else "Updated existing user ") +
                          f"{user} with email {options['email']} and NEW password, "
                          f"belonging to the {group} group.")
        return password
