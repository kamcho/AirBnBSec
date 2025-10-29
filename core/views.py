from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .utils import verify_kra_details

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
        
        if not kra_pin:
            return JsonResponse({
                'success': False,
                'message': 'KRA PIN is required'
            }, status=400)
            
        # Call the verification function
        result = verify_kra_details(kra_pin)
        
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
