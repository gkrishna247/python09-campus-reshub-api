from django.core.management.base import BaseCommand
from django.conf import settings
from apps.accounts.models import User
from apps.audit.models import create_audit_log
from decouple import config

class Command(BaseCommand):
    help = 'Seeds the database with an initial Admin user.'

    def handle(self, *args, **options):
        admin_email = config('ADMIN_EMAIL', default='sysadmin@ksrct.net')
        admin_password = config('ADMIN_PASSWORD')
        
        if not admin_password:
             self.stdout.write(self.style.ERROR("ADMIN_PASSWORD environment variable not set. Cannot seed admin."))
             return

        if User.all_objects.filter(email=admin_email).exists():
            self.stdout.write(self.style.WARNING("Admin user already exists. Skipping."))
        else:
            admin_user = User.objects.create_user(
                email=admin_email,
                name="System Administrator",
                password=admin_password,
                role="ADMIN",
                account_status="ACTIVE",
                approval_status="APPROVED",
                is_email_verified=True,
                is_staff=True,
                is_superuser=True
            )
            
            create_audit_log(
                actor=None,
                action="ADMIN_SEEDED",
                target_entity_type="user",
                target_entity_id=admin_user.id
            )
            
            self.stdout.write(self.style.SUCCESS("Admin user created successfully."))
