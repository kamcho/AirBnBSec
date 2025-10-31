from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from users.models import Client, ClientContact
from home.models import SecurityIncident
import json

@csrf_exempt
@require_http_methods(["POST"])
def save_verified_client(request):
    try:
        data = json.loads(request.body)
        id_number = data.get('id_number')
        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()

        if not id_number or not id_number.strip():
            return JsonResponse({'error': 'ID number is required'}, status=400)
            
        # Clean and validate ID number
        id_number = id_number.strip()
        if not id_number.isdigit() or len(id_number) < 6 or len(id_number) > 10:
            return JsonResponse(
                {'error': 'ID number must be 6-10 digits'}, 
                status=400
            )

        with transaction.atomic():
            # Try to get existing client by ID number
            client, created = Client.objects.get_or_create(
                id_number=id_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )

            # Update client details if they exist
            if not created:
                if first_name and not client.first_name:
                    client.first_name = first_name
                if last_name and not client.last_name:
                    client.last_name = last_name
                client.save()

            # Create or update email contact if provided
            if email and email.strip():
                ClientContact.objects.update_or_create(
                    client=client,
                    contact_type='email',
                    defaults={'contact': email.strip()}
                )

            # Create or update phone contact if provided
            if phone and phone.strip():
                # Remove any non-digit characters and ensure proper formatting
                phone_digits = ''.join(filter(str.isdigit, phone))
                if phone_digits.startswith('0') and len(phone_digits) == 10:
                    phone_digits = '254' + phone_digits[1:]  # Convert to international format
                elif len(phone_digits) == 9:
                    phone_digits = '254' + phone_digits  # Add country code if missing
                
                ClientContact.objects.update_or_create(
                    client=client,
                    contact_type='phone',
                    defaults={'contact': phone_digits}
                )

            return JsonResponse({
                'success': True,
                'client_id': client.id,
                'created': created
            })

    except Exception as e:
        return JsonResponse(
            {'error': f'Error saving client: {str(e)}'}, 
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
def set_incident_client(request, incident_id):
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')

        if not client_id:
            return JsonResponse({'error': 'Client ID is required'}, status=400)

        try:
            incident = SecurityIncident.objects.get(id=incident_id)
            client = Client.objects.get(id=client_id)
            
            incident.client = client
            incident.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Incident {incident_id} updated with client {client_id}'
            })
            
        except SecurityIncident.DoesNotExist:
            return JsonResponse(
                {'error': f'Incident with ID {incident_id} not found'}, 
                status=404
            )
        except Client.DoesNotExist:
            return JsonResponse(
                {'error': f'Client with ID {client_id} not found'}, 
                status=404
            )
            
    except Exception as e:
        return JsonResponse(
            {'error': f'Error updating incident: {str(e)}'}, 
            status=500
        )
