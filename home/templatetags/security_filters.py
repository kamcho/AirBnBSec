from django import template
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

register = template.Library()

@register.filter(name='mask_name')
def mask_name(value, arg):
    """
    Mask a name if the user is not the creator, admin, or doesn't have an active subscription.
    Format: First letter + ****** + last letter
    
    Usage: {{ name|mask_name:"user,incident" }}
    """
    if not value:
        return ""
    
    try:
        user, incident = arg.split(',')
        from django.template import Variable
        user = Variable(user).resolve()
        incident = Variable(incident).resolve()
        
        # If user is the creator or an admin, show full name
        if user and incident and (user == incident.reported_by or getattr(user, 'is_superuser', False)):
            return value
            
        # Strict subscription check: must be active and not expired
        try:
            subscription = user.subscription
            if getattr(subscription, 'is_active', False):
                return value
        except Exception:
            pass
            
    except Exception as e:
        # If there's any error in processing, mask the name for security
        pass
        
    # Mask the name
    if len(value) <= 2:
        return value[0] + '*' * (len(value) - 1) if value else ""
        
    return value[0] + '*' * (len(value) - 2) + value[-1] if len(value) > 1 else value


@register.filter(name='mask_person_name')
def mask_person_name(value):
    """
    Mask a person's name without needing context.
    Format: First letter + ****** + last letter
    """
    if not value:
        return ""
    if len(value) <= 2:
        return value[0] + '*' * (len(value) - 1) if value else ""
    return value[0] + '*' * (len(value) - 2) + value[-1] if len(value) > 1 else value


@register.simple_tag
def can_view_offender_name(user, incident):
    """
    Return True if the user can view the offender's full name.
    Rules: creator, admin, or has a strictly active subscription (is_active and not expired).
    """
    try:
        if not user or getattr(user, 'is_anonymous', False):
            return False
        if getattr(user, 'is_superuser', False):
            return True
        if incident and user == getattr(incident, 'reported_by', None):
            return True
        # Strict subscription: active and not expired
        try:
            subscription = user.subscription
            if getattr(subscription, 'is_active', False):
                return True
        except Exception:
            return False
        return False
    except Exception:
        return False


@register.filter(name='has_active_subscription')
def has_active_subscription(user):
    """Return True if user has an active (not expired) subscription."""
    try:
        if not user or getattr(user, 'is_anonymous', False):
            return False
        subscription = getattr(user, 'subscription', None)
        return bool(subscription and getattr(subscription, 'is_active', False))
    except Exception:
        return False
