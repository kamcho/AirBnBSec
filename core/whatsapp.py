"""
Simple WhatsApp Echo Handler
Receives messages and echoes them back
"""
import os
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv
from openai import OpenAI
from .utils import verify_kra_details
from home.models import SecurityIncident
from users.models import Client, PersonalProfile
from users.models import Subscription
from .models import VerificationRequest, FreeTrial
import re
from django.urls import reverse
from django.conf import settings
from django.utils import timezone


def _phone_variants(raw_phone):
    """Generate common variants for matching stored phone numbers."""
    if not raw_phone:
        return []
    p = str(raw_phone).strip()
    variants = set()
    # Raw and trimmed
    variants.add(p)
    variants.add(p.replace('whatsapp:', ''))
    # Ensure no plus
    p_np = p.replace('+', '')
    variants.add(p_np)
    # Add + variant
    variants.add('+' + p_np)
    # If startswith 2547..., add 07...
    if p_np.startswith('2547') and len(p_np) >= 12:
        variants.add('0' + p_np[3:])
    # If startswith 07..., add 2547...
    if p_np.startswith('07') and len(p_np) >= 10:
        variants.add('254' + p_np[1:])
        variants.add('+254' + p_np[1:])
    return list(variants)

def extract_id_number(message):
    """
    Extract ID number from message
    Returns the ID number or None
    """
    # Look for patterns like "A123456789X", "629383933", etc.
    # KRA PIN format: Starts with letter, ends with letter, digits in between
    kra_pattern = r'[A-Z]\d{9}[A-Z0-9]'
    # National ID format: 8-10 digits
    national_id_pattern = r'\d{7,10}'
    
    # Try KRA PIN first
    match = re.search(kra_pattern, message)
    if match:
        print(f"📋 Extracted KRA PIN: {match.group()}")
        return match.group()
    
    # Try National ID
    match = re.search(national_id_pattern, message)
    if match:
        print(f"📋 Extracted ID: {match.group()}")
        return match.group()
    
    print("⚠️ No ID number found in message")
    return None


def detect_intent(message):
    """
    Detect user intent from message using OpenAI
    
    Returns:
        dict: {
            'intent_id': str,  # e.g., 'verify', 'report', 'view', 'help', 'unknown'
            'message': str      # Original message
        }
    """
    try:
        # Load environment
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path, override=True)
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("⚠️ No OpenAI API key found, using fallback")
            return {
                'intent_id': 'unknown',
                'message': message
            }
        
        # Initialize OpenAI
        client = OpenAI(api_key=api_key)
        
        # System prompt for intent detection
        system_prompt = """You are an intent classifier for a security incident management system.

Classify the user's message into one of these intents:
- verify: User wants to verify/check someone (e.g., "verify KRA PIN", "check client")
- report: User wants to report an incident or issue
- view: User wants to view/list something (e.g., "show incidents", "list reports")
- help: User is asking for help or information
- unknown: Intent doesn't fit any category

Return ONLY the intent ID, nothing else."""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        intent_id = response.choices[0].message.content.strip().lower()
        
        # Validate intent_id
        valid_intents = ['verify', 'report', 'view', 'help', 'unknown']
        if intent_id not in valid_intents:
            intent_id = 'unknown'
        
        print(f"🔍 OpenAI detected intent: {intent_id}")
        
        return {
            'intent_id': intent_id,
            'message': message
        }
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        # Fallback to simple detection
        message_lower = message.lower()
        if any(word in message_lower for word in ['verify', 'verification', 'check', 'validate']):
            intent_id = 'verify'
        elif any(word in message_lower for word in ['report', 'incident', 'issue', 'problem']):
            intent_id = 'report'
        elif any(word in message_lower for word in ['view', 'show', 'list', 'see', 'get']):
            intent_id = 'view'
        elif any(word in message_lower for word in ['help', 'how', 'what', 'info']):
            intent_id = 'help'
        else:
            intent_id = 'unknown'
        
        return {
            'intent_id': intent_id,
            'message': message
        }


def send_message(to_phone, message):
    """Send WhatsApp message"""
    print("\n" + "="*50)
    print("🔍 DEBUG: Starting send_message function")
    print(f"📞 To: {to_phone}")
    print(f"📝 Message length: {len(message)} chars")
    
    # Load env
    print("\n🔄 Loading environment variables...")
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    print(f"📁 .env path: {env_path}")
    
    if os.path.exists(env_path):
        print("✅ .env file found")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print("❌ .env file NOT found!")
    
    # Get credentials
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '104040046094231')
    
    print(f"\n🔑 Access Token: {'****' + access_token[-4:] if access_token else '❌ NOT FOUND'}")
    print(f"📱 Phone Number ID: {phone_number_id}")
    
    if not access_token:
        print("❌ ERROR: No access token found in environment")
        return {'success': False, 'error': 'No access token'}
    
    # Prepare request
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    print(f"\n🌐 API Endpoint: {url}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_phone,
        'type': 'text',
        'text': {
            'preview_url': False,
            'body': message
        }
    }
    
    print("\n📤 Sending message...")
    print(f"📞 To: {to_phone}")
    print(f"📝 Message (first 100 chars): {message[:100]}...")
    
    try:
        print("\n🔄 Making API request...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"\n📥 Response received")
        print(f"🔢 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📦 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Message sent successfully!")
            return {'success': True}
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return {
                'success': False, 
                'status_code': response.status_code,
                'error': response.text
            }
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Exception:")
        print(f"Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
        return {'success': False, 'error': str(e)}
        
    except Exception as e:
        print(f"\n❌ Unexpected Error:")
        print(f"Type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    
    finally:
        print("\n" + "="*50 + "\n")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """Webhook handler"""
    
    if request.method == 'GET':
        # Webhook verification
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path, override=True)
        
        verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'test123')
        
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        print("\n" + "=" * 70)
        print("🔍 WEBHOOK VERIFICATION")
        print(f"Mode: {mode}")
        print(f"Token: {token}")
        print(f"Expected: {verify_token}")
        print(f"Match: {token == verify_token}")
        print("=" * 70)
        
        if mode == 'subscribe' and token == verify_token:
            print("✅ VERIFIED!")
            return HttpResponse(challenge)
        else:
            print("❌ FAILED")
            return HttpResponse('Verification failed', status=403)
    
    elif request.method == 'POST':
        # Handle incoming messages
        print("\n" + "=" * 70)
        print("🔔 MESSAGE RECEIVED (POST)")
        print("=" * 70)
        print(f"Request body length: {len(request.body)}")
        print(f"Content-Type: {request.content_type}")
        
        try:
            body = json.loads(request.body)
            print("\n📦 Full webhook payload:")
            print(json.dumps(body, indent=2))
            print("=" * 70)
            
            # Extract message
            if 'entry' in body:
                print("✅ Found 'entry' in body")
                for entry in body['entry']:
                    print(f"📂 Processing entry: {entry}")
                    changes = entry.get('changes', [])
                    print(f"📋 Found {len(changes)} changes")
                    
                    for change in changes:
                        print(f"🔄 Change field: {change.get('field')}")
                        if change.get('field') == 'messages':
                            print("✅ Found messages field")
                            value = change.get('value', {})
                            print(f"📦 Value keys: {value.keys()}")
                            
                            if 'messages' in value:
                                print(f"📨 Found {len(value.get('messages', []))} messages")
                                for message in value['messages']:
                                    message_text = message.get('text', {}).get('body', '')
                                    sender_phone = message.get('from', '').replace('whatsapp:', '')
                                    
                                    print(f"\n📨 From: {sender_phone}")
                                    print(f"📨 Message: {message_text}")
                                    
                                    # Detect intent
                                    intent_result = detect_intent(message_text)
                                    intent_id = intent_result['intent_id']
                                    print(f"🎯 Intent ID: {intent_id}")
                                    
                                    # Handle verify intent
                                    if intent_id == 'verify':
                                        print("🔍 Processing verification request...")
                                        
                                        # Extract ID number
                                        id_number = extract_id_number(message_text)
                                        
                                        if id_number:
                                            print(f"📋 Verifying ID: {id_number}")

                                            # First check if user is registered
                                            resolved_user = None
                                            variants = _phone_variants(sender_phone)
                                            profile = PersonalProfile.objects.filter(phone__in=variants).select_related('user').first()
                                            
                                            if not (profile and profile.user):
                                                # Unregistered user - send registration message
                                                registration_url = getattr(settings, 'SITE_URL', 'https://tourske.com').rstrip('/') + '/register/'
                                                response_message = (
                                                    "🔒 *Account Required*\n\n"
                                                    "You need to register an account to use our verification service.\n\n"
                                                    "📱 *How to get started:*\n"
                                                    "1. Visit our website: https://tourske.com\n"
                                                    "2. Create your free account\n"
                                                    "3. Start verifying IDs instantly!\n\n"
                                                    "💡 *Why register?*\n"
                                                    "• Verify clients securely\n"
                                                    "• Get free trial for testing\n"
                                                    "• Track your verification history\n"
                                                    "• Get instant results\n\n"
                                                    f"👉 Register here: {registration_url}"
                                                )
                                                send_message(sender_phone, response_message)
                                                return JsonResponse({'status': 'ok'})
                                            
                                            try:
                                                # If we get here, user is registered
                                                resolved_user = profile.user
                                                using_trial = False
                                                
                                                print(
                                                    "[whatsapp_webhook] system checking subscription for user",
                                                    getattr(resolved_user, 'email', resolved_user.id),
                                                    "of phone number",
                                                    sender_phone,
                                                    flush=True
                                                )
                                                subscription = getattr(resolved_user, 'subscription', None)
                                                print(
                                                    "[whatsapp_webhook] subscription status:",
                                                    {"has_sub": bool(subscription), "is_active": bool(subscription and subscription.is_active)},
                                                    flush=True
                                                )
                                                
                                                if not (subscription and subscription.is_active):
                                                    trial, created = FreeTrial.objects.get_or_create(user=resolved_user)
                                                    if created:
                                                        trial.count = 3
                                                        trial.expiry = timezone.now() + timezone.timedelta(days=7)
                                                        trial.save(update_fields=['count', 'expiry'])
                                                        print("[whatsapp_webhook] trial initialized:", {"count": trial.count, "expiry": trial.expiry}, flush=True)
                                                    print(
                                                        "[whatsapp_webhook] freetrial status:",
                                                        {"exists": True, "count": getattr(trial, 'count', None), "expiry": getattr(trial, 'expiry', None)},
                                                        flush=True
                                                    )
                                                    
                                                    # Check trial status
                                                    trial_expired = trial.expiry and timezone.now() > trial.expiry
                                                    trial_exhausted = (trial.count or 0) <= 0
                                                    
                                                    print(f"[whatsapp_webhook] Trial check - Expired: {trial_expired}, Count: {trial.count}, Exhausted: {trial_exhausted}", flush=True)
                                                    
                                                    # Only block if both expired AND no count left
                                                    if trial_expired and trial_exhausted:
                                                        base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                                                        payment_url = getattr(settings, 'PAYMENT_URL', '').strip()
                                                        if not payment_url:
                                                            try:
                                                                pay_path = reverse('payments:pay')  # use named URL if defined
                                                            except Exception:
                                                                pay_path = '/api/payments/pay/'
                                                            payment_url = f"https://tourske.com/api/payments/pay/"
                                                        msg = (
                                                            "🚫 Your free trial has ended.\n\n"
                                                            "You've reached the limit of complimentary verifications. To keep protecting your property and guests, upgrade now to unlock unlimited checks and instant alerts.\n\n"
                                                            "✅ Fast, reliable verifications\n"
                                                            "🛡️ Reduce fraud and risky bookings\n"
                                                            "📊 Access incident insights\n\n"
                                                            f"👉 Subscribe here: {payment_url}\n\n"
                                                            "For ksh 100 only per month"
                                                        )
                                                        print("[whatsapp_webhook] trial blocked send message", flush=True)
                                                        _ = send_message(sender_phone, msg)
                                                        return JsonResponse({'status': 'ok'})
                                                    using_trial = True
                                            except Exception as dbg_e:
                                                print("[whatsapp_webhook] debug check failed:", dbg_e, flush=True)
                                            
                                            # Create verification request record
                                            verification_request = VerificationRequest(
                                                requester_phone=sender_phone,
                                                id_number=id_number,
                                                response_data={"initial_request": message_text},
                                                source='whatsapp'
                                            )
                                            
                                            # Call KRA verification
                                            verification_result = verify_kra_details(id_number)
                                            
                                            if verification_result.get('success'):
                                                verified_name = verification_result.get('data', {}).get('name', 'Unknown')
                                                
                                                # Update verification request with success data
                                                verification_request.is_successful = True
                                                verification_request.response_data.update({
                                                    'verification_result': 'success',
                                                    'verified_name': verified_name,
                                                    'verification_data': verification_result.get('data', {})
                                                })
                                                verification_request.save()  # Save after updating with success data
                                                
                                                # Try to find and link client and incidents
                                                try:
                                                    client = Client.objects.get(id_number=id_number)
                                                    verification_request.client = client
                                                    
                                                    # Find incidents involving this client
                                                    incidents = SecurityIncident.objects.filter(
                                                        client=client
                                                    ).order_by('-reported_date')[:5]  # Get up to 5 most recent incidents
                                                    
                                                    if incidents.exists():
                                                        # Add related incidents to the verification request
                                                        verification_request.related_incidents.set(incidents)
                                                        
                                                        incidents_list = []
                                                        base_url = getattr(settings, 'SITE_URL', 'https://tourske.com')
                                                        
                                                        for incident in incidents:
                                                            incident_url = f"{base_url}{reverse('home:incident_detail', args=[incident.id])}"
                                                            incidents_list.append(
                                                                f"• [{incident.title}]({incident_url}) - {incident.get_status_display()}"
                                                            )
                                                        
                                                        incidents_text = "\n".join(incidents_list)
                                                        incident_heading = "\n\n⚠️ *Previous Incidents Involving This Client:*"
                                                    else:
                                                        incident_heading = "\n\n✅ No previous incidents found for this client."
                                                        incidents_text = ""
                                                    
                                                    # Save the verification request with client and incidents
                                                    verification_request.save()
                                                        
                                                except Client.DoesNotExist:
                                                    incident_heading = "\n\nℹ️ This client doesnt have previous reported offences."
                                                    incidents_text = ""
                                                    # Save the verification request even if no client is found
                                                    verification_request.save()
                                                
                                                # Build response
                                                response_message = (
                                                    "🔍 *Verification Result* 🔍\n\n"
                                                    f"✅ *Verification Successful!*\n"
                                                    f"📋 *Name:* {verified_name}\n"
                                                    f"🆔 *ID Number:* {id_number}"
                                                    f"{incident_heading}\n"
                                                    f"{incidents_text}\n\n"
                                                    "_If this does not match the person you're verifying, please report this incident immediately._\n\n"
                                                    "⚠️ *Suspicious Activity?*\n"
                                                    "If the verification details don't match the person's identification or if you suspect fraudulent activity, please report this incident at:\n"
                                                    "https://tourske.com/incidents/create/step1/\n\n"
                                                    "Your vigilance helps keep our community safe! 🛡️"
                                                )
                                                # Decrement trial on success
                                                if using_trial and resolved_user:
                                                    try:
                                                        trial = FreeTrial.objects.select_for_update().get(user=resolved_user)
                                                    except FreeTrial.DoesNotExist:
                                                        trial = None
                                                    if trial:
                                                        before = trial.count or 0
                                                        trial.count = max(0, before - 1)
                                                        trial.save(update_fields=['count'])
                                                        print("[whatsapp_webhook] trial decremented:", {"before": before, "after": trial.count}, flush=True)
                                                        response_message += f"\n\n🆓 Free trial remaining: {trial.count}"
                                                
                                                # Send the response message
                                                print(f"✅ Verified: {verified_name}")
                                                send_message(sender_phone, response_message)
                                                print(f"📨 Sent verification response to {sender_phone}")
                                            else:
                                                # Update verification request with failure data
                                                error_msg = verification_result.get('message', 'Verification failed')
                                                verification_request.is_successful = False
                                                verification_request.response_data.update({
                                                    'verification_result': 'failed',
                                                    'error': error_msg,
                                                    'verification_data': verification_result
                                                })
                                                verification_request.save()
                                                
                                                response_message = (
                                                    "❌ *Verification Failed*\n\n"
                                                    f"We couldn't verify the provided ID: {id_number}\n\n"
                                                    f"*Reason:* {error_msg}\n\n"
                                                    "⚠️ *Next Steps:*\n"
                                                    "1. Double-check the ID number for any typos\n"
                                                    "2. If the ID is correct but verification fails, the person may be using invalid credentials\n\n"
                                                    "*For your safety, we recommend:*\n"
                                                    "• Do not proceed with any transactions\n"
                                                    "• Report this incident at: https://tourske.com/incidents/create/step1/\n"
                                                    "• Contact support if you need assistance"
                                                )
                                                print(f"❌ Verification failed: {error_msg}")
                                                response_message = (
                                                    "❌ *Verification Failed*\n\n"
                                                    f"We couldn't verify the provided ID: {id_number}\n\n"
                                                    f"*Reason:* {error_msg}\n\n"
                                                    "⚠️ *Next Steps:*\n"
                                                    "1. Double-check the ID number for any typos\n"
                                                    "2. If the ID is correct but verification fails, the person may be using invalid credentials\n\n"
                                                    "*For your safety, we recommend:*\n"
                                                    "• Do not proceed with any transactions\n"
                                                    "• Report this incident at: https://tourske.com/incidents/create/step1/\n"
                                                    "• Contact support if you need assistance"
                                                )
                                        else:
                                            # Create a failed verification request for tracking
                                            VerificationRequest.objects.create(
                                                requester_phone=sender_phone,
                                                id_number='',
                                                is_successful=False,
                                                response_data={
                                                    'error': 'No valid ID number found',
                                                    'original_message': message_text
                                                },
                                                source='whatsapp'
                                            )
                                            response_message = "⚠️ Please provide an ID number to verify.\n\nExample: 'verify A123456789X'"
                                            print("⚠️ No ID number found")
                                    
                                    elif intent_id == 'report':
                                        response_message = (
                                            "📝 *Report an Incident* 📝\n\n"
                                            "To report a security incident, please visit our reporting portal and follow these steps:\n\n"
                                            "1. *Access the Form*: Go to https://tourske.com/incidents/create/step1/\n"
                                            "2. *Provide Details*: Fill in all required information about the incident\n"
                                            "3. *Upload Evidence*: Attach any relevant photos, documents, or screenshots\n"
                                            "4. *Submit Report*: Review and submit your report\n\n"
                                            "ℹ️ *What to include in your report:*\n"
                                            "• Date and time of the incident\n"
                                            "• Location or property address\n"
                                            "• Description of what happened\n"
                                            "• Any involved parties' information\n\n"
                                            "Your report helps us maintain a safe community. Thank you for your cooperation!"
                                        )
                                    else:
                                        # Default response for other intents
                                        response_message = f"Detected Intent: {intent_id}"
                                    
                                    print(f"💬 Sending response: {response_message}")
                                    result = send_message(sender_phone, response_message)
                                    
                                    if result.get('success'):
                                        print(f"✅ Response sent! (Intent: {intent_id})")
                                    else:
                                        print(f"❌ Failed: {result.get('error')}")
                            else:
                                print("❌ No 'messages' key in value")
                        else:
                            print(f"⚠️ Not a messages field: {change.get('field')}")
            else:
                print("❌ No 'entry' key in body")
            
            return JsonResponse({'status': 'ok'})
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Bad request'}, status=400)
