"""
Quick test to send a WhatsApp message
Run this to test if your credentials are working
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AirBnBSec.settings')
django.setup()

from core.whatsapp import send_whatsapp_message
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_send_message():
    """Test sending a WhatsApp message"""
    
    print("=" * 70)
    print("WHATSAPP MESSAGE TEST")
    print("=" * 70)
    print()
    
    # Your phone number (as it appears in the curl - 254742134431)
    phone_number = "254742134431"
    
    # Test message
    test_message = """🤖 Testing WhatsApp Integration!

✅ This is a test message from your AirBnBSec system.

Features:
• Intent detection using OpenAI
• Automatic verification handling
• KRA PIN verification
• Real-time responses

Try sending: "verify KRA PIN > A123456789X" to test verification!"""
    
    print(f"Sending message to: {phone_number}")
    print(f"Message: {test_message[:50]}...")
    print()
    
    result = send_whatsapp_message(phone_number, test_message)
    
    print("=" * 70)
    print("RESULT:")
    print("=" * 70)
    
    if result.get('success'):
        print("✅ Message sent successfully!")
        print(f"Message ID: {result.get('message_id')}")
    else:
        print("❌ Failed to send message")
        print(f"Error: {result.get('error')}")
        print(f"Status Code: {result.get('status_code')}")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    test_send_message()




