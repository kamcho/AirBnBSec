import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views import View
from django.utils import timezone
from .models import MpesaTransaction
from .mpesa_utils import stk_push

class PaymentView(View):
    """View to display the payment page"""
    def get(self, request, *args, **kwargs):
        # Get user's phone number from profile if it exists
        phone_number = ''
        if hasattr(request.user, 'profile') and request.user.profile.phone:
            # Remove any non-digit characters and take last 9 digits
            phone_digits = ''.join(filter(str.isdigit, request.user.profile.phone))
            phone_number = phone_digits[-9:]  # Take last 9 digits in case of country code
            
        return render(request, 'payments/make_payment.html', {
            'user_phone': phone_number
        })
@login_required
def initiate_payment(request):
    """View to initiate M-Pesa STK push and save the payment response"""
    if request.method == 'POST':
        try:
            print("\n=== INITIATE PAYMENT DEBUG ===")
            print(f"User: {request.user} (ID: {request.user.id if request.user.is_authenticated else 'Anonymous'})")
            
            # Parse request data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            print(f"Request data: {data}")
                
            phone_number = data.get('phone_number')
            amount = 1  # Fixed amount of 1 KSH for testing
            account_reference = data.get('account_reference', f'AIRBNBSEC{request.user.id}')
            description = data.get('description', 'AirBnBSec Service Fee')
            
            if not phone_number:
                return JsonResponse(
                    {'error': 'Phone number is required'}, 
                    status=400
                )
            
            # Format phone number if needed (remove + or 0 and add 254)
            phone_number = str(phone_number).strip()
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif len(phone_number) == 9:
                phone_number = '254' + phone_number
            
            # Validate phone number
            if not (phone_number.startswith('2547') and len(phone_number) == 12 and phone_number[1:].isdigit()):
                return JsonResponse(
                    {'error': 'Please enter a valid M-Pesa phone number starting with 07, +254 or 254'}, 
                    status=400
                )
            
            # Create a new transaction
            print(f"Creating new transaction for user: {request.user}")
            
            # First try to find an existing pending transaction for this user
            existing_transaction = MpesaTransaction.objects.filter(
                user=request.user,
                status='pending',
                created_at__gte=timezone.now() - timezone.timedelta(minutes=30)
            ).first()
            
            if existing_transaction:
                print(f"Found existing pending transaction {existing_transaction.id}, reusing it")
                transaction = existing_transaction
                transaction.user = request.user  # Ensure user is set
                transaction.phone_number = phone_number
                transaction.amount = amount
                transaction.account_reference = account_reference
                transaction.transaction_desc = description
            else:
                # Create a new transaction if no existing one found
                transaction = MpesaTransaction(
                    user=request.user,
                    phone_number=phone_number,
                    amount=amount,
                    account_reference=account_reference,
                    transaction_desc=description,
                    status='pending'
                )
                print(f"Created new transaction for user: {request.user.id} - {request.user}")
            
            # Save the transaction to get an ID
            # Save the transaction to get an ID
            try:
                transaction.save()
                print(f"Transaction saved successfully with user: {transaction.user} (ID: {transaction.user.id if transaction.user else 'None'})")
                print(f"Transaction details - ID: {transaction.id}, Status: {transaction.status}, Created: {transaction.created_at}")
            except Exception as e:
                print(f"Error saving transaction: {str(e)}")
                # Log the full traceback for debugging
                import traceback
                traceback.print_exc()
                return JsonResponse(
                    {
                        'error': 'Failed to save transaction',
                        'details': str(e)
                    }, 
                    status=500
                )

# Verify the user was saved
            transaction.refresh_from_db()
            print(f"Transaction after save - ID: {transaction.id}, User: {transaction.user} (ID: {transaction.user.id if transaction.user else 'None'})")
            
            # Include the transaction ID in the account reference to track it in callbacks
            account_reference_with_id = f"{account_reference}_{transaction.id}"
            
            # Initiate STK push
            response = stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference_with_id,
                description=description,
                user=request.user
            )
            
            # Save the response to the transaction
            if 'error' in response:
                transaction.status = 'failed'
                transaction.result_code = 'ERROR'
                transaction.result_description = response.get('error', 'Unknown error')
                transaction.save()
                return JsonResponse(
                    {'error': response['error']}, 
                    status=400
                )
            
            # Update transaction with response details
            merchant_request_id = response.get('merchant_request_id')
            checkout_request_id = response.get('checkout_request_id')
            
            # Check if a transaction with this checkout_request_id already exists
            if checkout_request_id:
                try:
                    # Try to get an existing transaction with this checkout_request_id
                    existing_with_checkout = MpesaTransaction.objects.get(
                        checkout_request_id=checkout_request_id
                    )
                    # If we get here, a transaction with this ID exists
                    if existing_with_checkout.id != transaction.id:
                        # If it's a different transaction, delete the new one and use the existing
                        transaction.delete()
                        transaction = existing_with_checkout
                        print(f"Using existing transaction {transaction.id} with checkout_request_id {checkout_request_id}")
                except MpesaTransaction.DoesNotExist:
                    # No existing transaction with this ID, update the current one
                    transaction.merchant_request_id = merchant_request_id
                    transaction.checkout_request_id = checkout_request_id
                    transaction.save()
            else:
                # If no checkout_request_id, just save the merchant_request_id
                transaction.merchant_request_id = merchant_request_id
                transaction.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'transaction_id': str(transaction.id),
                'checkout_request_id': checkout_request_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON data'}, 
                status=400
            )
        except Exception as e:
            print(f"Error in initiate_payment: {str(e)}")
            return JsonResponse(
                {'error': 'An error occurred while processing your request'}, 
                status=500
            )
    
    return JsonResponse(
        {'error': 'Only POST requests are allowed'}, 
        status=405
    )
@csrf_exempt







@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa callback"""
    print("\n=== MPESA CALLBACK DEBUG ===")
    print(f"Request user: {request.user} (ID: {request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'})")
    
    try:
        # Log the raw request body for debugging
        body = request.body.decode('utf-8')
        callback_data = json.loads(body)
        
        # Log the callback data (use logging in production)
        print("Raw callback data:", json.dumps(callback_data, indent=2))
        
        # Extract the result code and description
        result = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = str(result.get('ResultCode'))  # Convert to string for consistency
        result_desc = result.get('ResultDesc', '').lower()
        checkout_request_id = result.get('CheckoutRequestID')
        
        if not checkout_request_id:
            print("Error: No CheckoutRequestID in callback data")
            return JsonResponse(
                {'status': 'error', 'message': 'Missing CheckoutRequestID'}, 
                status=400
            )
        
        # Find the transaction by checkout_request_id first
        transaction = None
        try:
            print(f"Looking up transaction with checkout_request_id: {checkout_request_id}")
            transaction = MpesaTransaction.objects.get(
                checkout_request_id=checkout_request_id
            )
            print(f"Found transaction by checkout_request_id: {transaction.id}")
        except MpesaTransaction.DoesNotExist:
            print(f"No transaction found with checkout_request_id: {checkout_request_id}")
        
        # If not found by checkout_request_id, try to find by account_reference
        if not transaction and 'account_reference' in result:
            account_reference = result['account_reference']
            # Check if account_reference contains our transaction ID (format: AIRBNBSEC{user_id}_{transaction_id})
            if '_' in account_reference:
                try:
                    transaction_id = int(account_reference.split('_')[-1])
                    transaction = MpesaTransaction.objects.get(id=transaction_id)
                    print(f"Found transaction by ID from account_reference: {transaction.id}")
                    
                    # Update the checkout_request_id for future reference
                    transaction.checkout_request_id = checkout_request_id
                    transaction.save(update_fields=['checkout_request_id'])
                except (ValueError, MpesaTransaction.DoesNotExist) as e:
                    print(f"Could not find transaction by account_reference: {e}")
        
        if not transaction:
            print(f"Error: Could not find transaction with checkout_request_id {checkout_request_id}")
            return JsonResponse(
                {'status': 'error', 'message': 'Transaction not found'}, 
                status=404
            )
        
        print(f"Processing transaction ID: {transaction.id}")
        print(f"Current transaction user: {transaction.user} (ID: {transaction.user.id if transaction.user else 'None'})")
        print(f"Current status: {transaction.status}")
        
        # If transaction is already completed, don't process again
        if transaction.status == 'completed':
            print(f"Transaction {transaction.id} is already marked as completed")
            return JsonResponse({
                'status': 'success', 
                'message': 'Callback already processed',
                'transaction_id': str(transaction.id)
            })
            
        # Update transaction status based on result code
        if result_code == '0':
            # Success
            callback_metadata = result.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            # Extract payment details from callback
            payment_data = {}
            for item in items:
                name = item.get('Name')
                if name:
                    payment_data[name] = item.get('Value')
            
            # Update transaction with payment details
            transaction.mpesa_receipt_number = payment_data.get('MpesaReceiptNumber')
            
            # Update phone number if available in callback
            if 'PhoneNumber' in payment_data:
                transaction.phone_number = str(payment_data['PhoneNumber'])
            
            # Ensure the user is set if it's not already
            if transaction.user is None and hasattr(request, 'user') and request.user.is_authenticated:
                transaction.user = request.user
            
            # Update transaction date if available
            if 'TransactionDate' in payment_data:
                try:
                    transaction_date = str(payment_data['TransactionDate'])
                    transaction.transaction_date = datetime.strptime(
                        transaction_date, '%Y%m%d%H%M%S'
                    )
                except (ValueError, TypeError) as e:
                    print(f"Error parsing transaction date: {e}")
            
            # Update transaction details
            transaction.status = 'completed'
            transaction.result_code = '0'
            transaction.result_description = 'Payment completed successfully'
            
            # Update user's subscription
            if transaction.user:
                from django.utils import timezone
                from datetime import timedelta
                from users.models import Subscription
                
                user = transaction.user
                now = timezone.now()
                
                try:
                    # Try to get existing subscription
                    subscription = user.subscription
                    # If subscription exists and is not expired, extend from expiry date
                    if subscription.expiry and subscription.expiry > now:
                        new_expiry = subscription.expiry + timedelta(days=30)
                    else:
                        new_expiry = now + timedelta(days=30)
                    
                    # Update subscription
                    subscription.expiry = new_expiry
                    subscription.save()
                    
                except Subscription.DoesNotExist:
                    # Create new subscription if it doesn't exist
                    new_expiry = now + timedelta(days=30)
                    subscription = Subscription.objects.create(
                        user=user,
                        expiry=new_expiry
                    )
                    
                print(f"Updated subscription for user {user.id}. New expiry: {new_expiry}")
            
            transaction.save()
            print(f"Transaction {transaction.id} marked as completed")
            
        else:
            # Handle different failure cases
            if result_code == '1032':
                # Request cancelled by user
                transaction.status = 'cancelled'
                transaction.result_description = 'Payment was cancelled by the user'
                
                # Ensure the user is set if it's not already
                if transaction.user is None and hasattr(request, 'user') and request.user.is_authenticated:
                    transaction.user = request.user
            elif 'request cancelled by user' in result_desc:
                transaction.status = 'cancelled'
                transaction.result_description = 'Payment was cancelled by the user'
            elif 'insufficient funds' in result_desc:
                transaction.status = 'failed'
                transaction.result_description = 'Insufficient funds in M-Pesa account'
            else:
                transaction.status = 'failed'
                transaction.result_description = result_desc[:255]  # Truncate if too long
            
            transaction.result_code = result_code
            transaction.save()
            print(f"Transaction {transaction.id} marked as {transaction.status}: {transaction.result_description}")
            
        # Here you can trigger any post-payment actions
        # e.g., send email, update subscription, etc.
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Callback processed successfully',
            'transaction_id': str(transaction.id) if 'transaction' in locals() else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)}, 
            status=500
        )
def check_transaction_status(request, transaction_id):
    """Check the status of a transaction"""
    transaction = get_object_or_404(MpesaTransaction, id=transaction_id)
    
    # For security, ensure the user can only see their own transactions
    if request.user != transaction.user and not request.user.is_staff:
        return JsonResponse(
            {'error': 'Not authorized to view this transaction'}, 
            status=403
        )
    
    return JsonResponse({
        'transaction_id': transaction.id,
        'status': transaction.status,
        'mpesa_receipt_number': transaction.mpesa_receipt_number,
        'amount': str(transaction.amount),
        'phone_number': transaction.phone_number,
        'created_at': transaction.created_at.isoformat(),
        'updated_at': transaction.updated_at.isoformat(),
        'result_code': transaction.result_code,
        'result_description': transaction.result_description,
        'is_successful': transaction.is_successful()
    })
