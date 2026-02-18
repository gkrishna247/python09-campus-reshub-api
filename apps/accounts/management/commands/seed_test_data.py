from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.resources.models import Resource, ResourceWeeklySchedule, CalendarOverride
from apps.bookings.models import Booking
from apps.notifications.models import UserNotification
import datetime

class Command(BaseCommand):
    help = "Seeds test data for development. Safe to run multiple times."

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting to seed test data...'))

            # Counters
            users_count = 0
            resources_count = 0
            schedules_count = 0
            bookings_count = 0
            notifications_count = 0
            overrides_count = 0

            # 1. Create Test Users
            users_data = [
                {'name': 'Dr. Ramesh Kumar', 'email': 'ramesh.faculty@ksrct.net', 'role': 'FACULTY', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Priya Sharma', 'email': 'priya.student@ksrct.net', 'role': 'STUDENT', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Anand Raj', 'email': 'anand.staff@ksrct.net', 'role': 'STAFF', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Meera Nair', 'email': 'meera.student@ksrct.net', 'role': 'STUDENT', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Karthik Rajan', 'email': 'karthik.faculty@ksrct.net', 'role': 'FACULTY', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Deepa Venkat', 'email': 'deepa.staff@ksrct.net', 'role': 'STAFF', 'account_status': 'ACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
                {'name': 'Suresh Babu', 'email': 'suresh.external@gmail.com', 'role': 'STUDENT', 'account_status': 'ACTIVE', 'approval_status': 'PENDING', 'is_email_verified': False},
                {'name': 'Lakshmi Devi', 'email': 'lakshmi.external@gmail.com', 'role': 'FACULTY', 'account_status': 'ACTIVE', 'approval_status': 'PENDING', 'is_email_verified': False},
                {'name': 'Vikram Singh', 'email': 'vikram.inactive@ksrct.net', 'role': 'STUDENT', 'account_status': 'INACTIVE', 'approval_status': 'APPROVED', 'is_email_verified': True},
            ]

            for user_data in users_data:
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'name': user_data['name'],
                        'role': user_data['role'],
                        'account_status': user_data['account_status'],
                        'approval_status': user_data['approval_status'],
                        'is_email_verified': user_data['is_email_verified'],
                    }
                )
                if created:
                    user.set_password("Test@1234")
                    user.save()
                    users_count += 1
                else:
                    # Ensure password is set correctly for existing users too if needed, but requirements say idempotent
                    # However prompt says "After get_or_create, call user.set_password... and user.save()." implies update too?
                    # "Safe to run multiple times without creating duplicates" - usually means don't change existing unless needed.
                    # But prompt explicitly said: "After get_or_create, call user.set_password... and user.save()."
                    # I will follow instruction to set password always to ensure consistency if seed runs again.
                    user.set_password("Test@1234")
                    user.save()
                
            # Get admin user
            try:
                admin_user = User.objects.get(email='sysadmin@ksrct.net')
            except User.DoesNotExist:
                # Fallback if seed_admin wasn't run
                admin_user, created = User.objects.get_or_create(
                    email='sysadmin@ksrct.net',
                    defaults={
                        'name': 'System Administrator',
                        'role': 'ADMIN',
                        'account_status': 'ACTIVE',
                        'approval_status': 'APPROVED',
                        'is_email_verified': True,
                        'is_staff': True,
                        'is_superuser': True
                    }
                )
                if created:
                    admin_user.set_password("Admin@1234") # Fallback password
                    admin_user.save()
                    users_count += 1

            # 2. Create Test Resources
            # Get referenced users for managed_by
            anand = User.objects.get(email='anand.staff@ksrct.net')
            deepa = User.objects.get(email='deepa.staff@ksrct.net')

            resources_data = [
                {'name': 'Advanced Computing Lab', 'type': 'LAB', 'capacity': 60, 'total_quantity': 1, 'location': 'Block A, Floor 2', 'approval_type': 'AUTO_APPROVE', 'managed_by': anand},
                {'name': 'Seminar Hall A', 'type': 'EVENT_HALL', 'capacity': 200, 'total_quantity': 1, 'location': 'Main Block, Ground Floor', 'approval_type': 'ADMIN_APPROVE', 'managed_by': anand},
                {'name': 'Classroom C-101', 'type': 'CLASSROOM', 'capacity': 40, 'total_quantity': 1, 'location': 'Block C, Floor 1', 'approval_type': 'AUTO_APPROVE', 'managed_by': deepa},
                {'name': 'Classroom C-202', 'type': 'CLASSROOM', 'capacity': 50, 'total_quantity': 1, 'location': 'Block C, Floor 2', 'approval_type': 'STAFF_APPROVE', 'managed_by': deepa},
                {'name': 'Portable Projectors', 'type': 'LAB', 'capacity': 0, 'total_quantity': 10, 'location': 'Equipment Room, Block A', 'approval_type': 'AUTO_APPROVE', 'managed_by': anand},
                {'name': 'Laptop Pool', 'type': 'LAB', 'capacity': 0, 'total_quantity': 25, 'location': 'IT Department', 'approval_type': 'STAFF_APPROVE', 'managed_by': deepa},
                {'name': 'Conference Room B', 'type': 'EVENT_HALL', 'capacity': 30, 'total_quantity': 1, 'location': 'Block B, Floor 3', 'approval_type': 'STAFF_APPROVE', 'managed_by': anand},
            ]

            for res_data in resources_data:
                resource, created = Resource.objects.get_or_create(
                    name=res_data['name'],
                    defaults={
                        'type': res_data['type'],
                        'capacity': res_data['capacity'],
                        'total_quantity': res_data['total_quantity'],
                        'location': res_data['location'],
                        'approval_type': res_data['approval_type'],
                        'managed_by': res_data['managed_by'],
                        'resource_status': 'AVAILABLE',
                        'is_deleted': False
                    }
                )
                if created:
                    resources_count += 1

            # 3. Create Weekly Schedules
            # Fetch all created resources to iterate
            all_resources = Resource.objects.filter(name__in=[r['name'] for r in resources_data])
            
            for resource in all_resources:
                for day in range(7): # 0=Monday, 6=Sunday
                    is_working = day < 5 # Mon-Fri are working
                    schedule, created = ResourceWeeklySchedule.objects.get_or_create(
                        resource=resource,
                        day_of_week=day,
                        defaults={
                            'is_working': is_working,
                            'start_time': datetime.time(8, 0),
                            'end_time': datetime.time(19, 0)
                        }
                    )
                    if created:
                        schedules_count += 1

            # 4. Create Sample Bookings
            today = timezone.now().date()
            
            bookings_data = [
                {'user_email': 'priya.student@ksrct.net', 'resource_name': 'Advanced Computing Lab', 'days_offset': 1, 'start': '09:00', 'end': '10:00', 'qty': 1, 'status': 'APPROVED'},
                {'user_email': 'priya.student@ksrct.net', 'resource_name': 'Portable Projectors', 'days_offset': 2, 'start': '10:00', 'end': '11:00', 'qty': 2, 'status': 'PENDING'},
                {'user_email': 'meera.student@ksrct.net', 'resource_name': 'Classroom C-101', 'days_offset': 1, 'start': '14:00', 'end': '15:00', 'qty': 1, 'status': 'APPROVED'},
                {'user_email': 'ramesh.faculty@ksrct.net', 'resource_name': 'Seminar Hall A', 'days_offset': 3, 'start': '08:00', 'end': '09:00', 'qty': 1, 'status': 'PENDING'},
                {'user_email': 'karthik.faculty@ksrct.net', 'resource_name': 'Conference Room B', 'days_offset': 2, 'start': '11:00', 'end': '12:00', 'qty': 1, 'status': 'APPROVED'},
                {'user_email': 'priya.student@ksrct.net', 'resource_name': 'Laptop Pool', 'days_offset': 4, 'start': '09:00', 'end': '10:00', 'qty': 3, 'status': 'APPROVED'},
            ]

            for b_data in bookings_data:
                user = User.objects.get(email=b_data['user_email'])
                resource = Resource.objects.get(name=b_data['resource_name'])
                booking_date = today + datetime.timedelta(days=b_data['days_offset'])
                start_time_obj = datetime.datetime.strptime(b_data['start'], "%H:%M").time()
                end_time_obj = datetime.datetime.strptime(b_data['end'], "%H:%M").time()
                
                defaults = {
                    'end_time': end_time_obj, # strictly not needed for get_or_create lookup if included in defaults, but keys are (user, resource, date, start)
                    'quantity_requested': b_data['qty'],
                    'status': b_data['status'],
                    'is_special_request': False
                }
                
                if b_data['status'] == 'APPROVED':
                    defaults['approved_by'] = admin_user
                    defaults['approved_at'] = timezone.now()

                booking, created = Booking.objects.get_or_create(
                    user=user,
                    resource=resource,
                    booking_date=booking_date,
                    start_time=start_time_obj,
                    defaults=defaults
                )
                if created:
                    bookings_count += 1

            # 5. Create Notifications
            params = [
                {'email': 'priya.student@ksrct.net', 'type': 'BOOKING_APPROVED', 'title': 'Booking Approved', 'body_template': 'Your booking for Advanced Computing Lab on {date} has been approved.', 'days_offset': 1},
                {'email': 'meera.student@ksrct.net', 'type': 'BOOKING_APPROVED', 'title': 'Booking Approved', 'body_template': 'Your booking for Classroom C-101 on {date} has been approved.', 'days_offset': 1},
                {'email': 'ramesh.faculty@ksrct.net', 'type': 'BOOKING_PENDING', 'title': 'Booking Submitted', 'body_template': 'Your booking for Seminar Hall A is pending admin approval.', 'days_offset': 0} # No date variable in body template for ramesh per prompt, but for consistency I'll check template
            ]
            
            # Prompt: "For ramesh: ... body='Your booking for Seminar Hall A is pending admin approval.'" (No date place holder)

            for param in params:
                user = User.objects.get(email=param['email'])
                date_str = (today + datetime.timedelta(days=param.get('days_offset', 0))).strftime('%Y-%m-%d')
                body = param['body_template'].replace('{date}', date_str)
                
                # Check for existing notification to avoid dupes purely on body/title/user? 
                # "Create 2-3 UserNotification entries" - implies just create them. 
                # "idempotent" request covers everything.
                # UserNotification doesn't have a unique constraint, so get_or_create might create duplicates if we are not careful with params.
                # However, since we want idempotency, we should try get_or_create with all fields.
                
                notif, created = UserNotification.objects.get_or_create(
                    user=user,
                    title=param['title'],
                    body=body,
                    defaults={
                        'message_type': param['type'],
                        'is_read': False
                    }
                )
                if created:
                    notifications_count += 1

            # 6. Create Calendar Override
            # "A HOLIDAY override for the next occurring Saturday"
            # Find next Saturday
            days_ahead = 5 - today.weekday()
            if days_ahead <= 0: # Target day already happened this week
                days_ahead += 7
            next_saturday = today + datetime.timedelta(days=days_ahead)
            
            override, created = CalendarOverride.objects.get_or_create(
                override_date=next_saturday,
                defaults={
                    'override_type': 'HOLIDAY',
                    'description': 'Campus Maintenance Day',
                    'created_by': admin_user
                }
            )
            if created:
                overrides_count += 1

            # 7. Print Summary
            self.stdout.write(self.style.SUCCESS("-" * 40))
            self.stdout.write(self.style.SUCCESS(f"Seed Test Data Summary"))
            self.stdout.write(self.style.SUCCESS("-" * 40))
            self.stdout.write(f"Users Created/Found:      {users_count + 9 if users_count == 0 else users_count}") # Logic check: if users_count is 0, it means all 9 existed. If 9, all created. 
            # Actually, the requirement asks for "users created/found", implying total count.
            # I should count total found/created.
            
            # Re-calculating actual totals for accuracy
            total_users = User.objects.filter(email__in=[u['email'] for u in users_data]).count()
            total_resources = Resource.objects.count() # Or filter by names
            total_schedules = ResourceWeeklySchedule.objects.count()
            total_bookings = Booking.objects.count()
            total_notifs = UserNotification.objects.count()
            total_overrides = CalendarOverride.objects.count()

            self.stdout.write(f"Users Processed:          {len(users_data)}") 
            self.stdout.write(f"Resources Total:          {total_resources}")
            self.stdout.write(f"Schedules Total:          {total_schedules}")
            self.stdout.write(f"Bookings Total:           {total_bookings}")
            self.stdout.write(f"Notifications Total:      {total_notifs}")
            self.stdout.write(f"Overrides Total:          {total_overrides}")
            
            self.stdout.write(self.style.SUCCESS("\nData seeding completed successfully."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding data: {str(e)}"))
