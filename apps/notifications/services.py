from apps.notifications.models import UserNotification
from apps.accounts.models import User

def create_notification(user, message_type, title, body, related_entity_type=None, related_entity_id=None):
    """
    Creates a notification for a specific user.
    """
    return UserNotification.objects.create(
        user=user,
        message_type=message_type,
        title=title,
        body=body,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id
    )

def notify_admins(message_type, title, body, related_entity_type=None, related_entity_id=None):
    """
    Creates notifications for all active and approved ADMIN users.
    """
    admins = User.objects.filter(role="ADMIN", account_status="ACTIVE", approval_status="APPROVED")
    notifications = []
    for admin in admins:
        notifications.append(UserNotification(
            user=admin,
            message_type=message_type,
            title=title,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        ))
    
    if notifications:
        UserNotification.objects.bulk_create(notifications)

def notify_faculty(message_type, title, body, related_entity_type=None, related_entity_id=None):
    """
    Creates notifications for all active and approved FACULTY users.
    """
    faculty = User.objects.filter(role="FACULTY", account_status="ACTIVE", approval_status="APPROVED")
    notifications = []
    for f in faculty:
        notifications.append(UserNotification(
            user=f,
            message_type=message_type,
            title=title,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        ))
        
    if notifications:
        UserNotification.objects.bulk_create(notifications)
