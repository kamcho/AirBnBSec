#!/usr/bin/env python3
"""Check what verify token is being used"""

import os
import sys
sys.path.insert(0, '/home/kali/Downloads/AirBnBSec')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AirBnBSec.settings')

# Load environment
from dotenv import load_dotenv
load_dotenv('/home/kali/Downloads/AirBnBSec/.env')

verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'not_found')

print("\n" + "=" * 70)
print("VERIFY TOKEN CHECK")
print("=" * 70)
print(f"WHATSAPP_VERIFY_TOKEN from .env: '{verify_token}'")
print(f"Length: {len(verify_token)}")
print("=" * 70)
print("\nUse this EXACT value (including any spaces) in Meta Dashboard")
print("Or set it to a simple value like 'test123'")



