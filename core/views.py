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
        print("[verify_kra] system checking subscription for user",
              getattr(user, 'email', user.id),
              "of phone number",
              requester_phone,
              flush=True)
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
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def verify_id_number(request, id_number):
    """
    API endpoint to verify a Kenyan National ID number
    
    Args:
        id_number (str): The Kenyan National ID number to verify (8-9 digits)
        
    Returns:
        JSON response with verification status and data
        {
            'success': bool,
            'data': {
                'name': str,  # Full name if verification successful
                'id_number': str  # The verified ID number
            },
            'message': str  # Status message
        }
    """
    from django.core.validators import RegexValidator
    from django.core.exceptions import ValidationError
    
    # Validate ID number format (8-9 digits)
    try:
        validate_id = RegexValidator(
            regex='^\d{7,9}$',
            message='ID number must be 8-9 digits',
            code='invalid_id_number'
        )
        validate_id(id_number)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    
    try:
        # Log the ID being verified
        print(f"\n=== ID Verification Request ===")
        print(f"ID Number: {id_number}")
        print("Using ID number directly for verification")
        print("==========================")
        
        # Use the ID number directly without adding A and Z
        kra_pin = id_number
        
        # Get the KRA verification result
        result = verify_kra_details(kra_pin)
        
        # Debug output
        print("\n=== KRA Verification Result ===")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Data: {result.get('data', {})}")
        print("============================")
        
        # Check if the KRA API returned an error
        kra_data = result.get('data', {})
        if not result.get('success') or 'ErrorCode' in kra_data or not kra_data.get('name'):
            error_msg = kra_data.get('ErrorMessage') or result.get('message') or 'Failed to verify ID with KRA'
            
            # Provide more user-friendly error messages
            if kra_data.get('ErrorCode') == '30002':
                error_msg = 'The provided ID number could not be verified with KRA. This could be because:\n' \
                          '1. The ID is not registered with KRA\n' \
                          '2. The ID is invalid or in an incorrect format\n' \
                          '3. There is an issue with the KRA verification service'
            
            print(f"KRA Verification Failed: {error_msg}")
            return JsonResponse({
                'success': False,
                'message': error_msg,
                'error_code': kra_data.get('ErrorCode')
            }, status=400)
            
        # If we get here, verification was successful
        return JsonResponse({
            'success': True,
            'data': {
                'name': kra_data.get('full_name', 'N/A'),
                'id_number': id_number
            },
            'message': 'ID verified successfully'
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error verifying ID: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
