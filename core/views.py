from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json

from .utils import verify_kra_details
from .models import FreeTrial
from users.models import Subscription, PersonalProfile

@csrf_exempt
@require_http_methods(["POST"])
def verify_kra(request):
    """
    API endpoint to verify KRA details
    
    Expected POST data:
    {
        "kra_pin": "A123456789X"  # KRA PIN to verify
    }
    
    Returns:
        JSON response with verification status and data
    """
    try:
        data = json.loads(request.body)
        kra_pin = data.get('kra_pin')
        requester_phone = data.get('phone') or data.get('requester_phone')
        print("[verify_kra] incoming:", {"kra_pin": kra_pin, "requester_phone": requester_phone, "is_auth": bool(getattr(request, 'user', None) and request.user.is_authenticated)}, flush=True)

        if not kra_pin:
            return JsonResponse({
                'success': False,
                'message': 'KRA PIN is required'
            }, status=400)

        # Resolve the user initiating the request
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        if not user and requester_phone:
            profile = PersonalProfile.objects.filter(phone=requester_phone).select_related('user').first()
            user = profile.user if profile else None

        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Could not resolve user. Login or provide a valid phone number.'
            }, status=401)
        else:
            try:
                print("[verify_kra] user resolved:", {"id": user.id, "email": getattr(user, 'email', None)}, flush=True)
            except Exception:
                print("[verify_kra] user resolved but logging failed", flush=True)

        # Check active subscription
        subscription = getattr(user, 'subscription', None)
        print("[verify_kra] subscription status:", {"has_sub": bool(subscription), "is_active": bool(subscription and subscription.is_active)}, flush=True)
        using_trial = False
        trial = None
        if not (subscription and subscription.is_active):
            # Handle free trial
            trial, created = FreeTrial.objects.get_or_create(user=user)
            print("[verify_kra] trial fetched/created:", {"created": created, "count": getattr(trial, 'count', None), "expiry": getattr(trial, 'expiry', None), "now": timezone.now()}, flush=True)
            if created:
                # Initialize default trial window
                trial.count = 3
                trial.expiry = timezone.now() + timedelta(days=7)
                trial.save(update_fields=['count', 'expiry'])
                print("[verify_kra] trial initialized:", {"count": trial.count, "expiry": trial.expiry}, flush=True)

            # Check expiry or exhausted count
            if (trial.expiry and timezone.now() > trial.expiry) or trial.count <= 0:
                print("[verify_kra] trial blocked:", {"expired": bool(trial.expiry and timezone.now() > trial.expiry), "count": trial.count}, flush=True)
                return JsonResponse({
                    'success': False,
                    'message': 'Your free trial is expired or used up.'
                }, status=402)

            using_trial = True

        # Call the verification function
        print("[verify_kra] calling verify_kra_details", {"kra_pin": kra_pin}, flush=True)
        result = verify_kra_details(kra_pin)
        print("[verify_kra] verification result:", {"success": result.get('success')}, flush=True)

        # On success, if using trial, decrement count
        if result.get('success') and using_trial and trial:
            before = trial.count or 0
            trial.count = max(0, before - 1)
            trial.save(update_fields=['count'])
            print("[verify_kra] trial decremented:", {"before": before, "after": trial.count}, flush=True)
        else:
            print("[verify_kra] no decrement:", {"using_trial": using_trial, "trial_exists": bool(trial), "success": bool(result.get('success'))}, flush=True)

        # Return appropriate status code based on verification result
        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
