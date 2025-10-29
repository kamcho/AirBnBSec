#!/bin/bash

# Test webhook verification

echo "Testing webhook verification..."
echo ""

# Your verify token - UPDATE THIS to match what you set in Meta Dashboard
VERIFY_TOKEN="test123"

echo "Testing with token: $VERIFY_TOKEN"
echo ""

curl -i "https://arhythmically-unciliated-danna.ngrok-free.dev/api/core/webhook/whatsapp/?hub.mode=subscribe&hub.verify_token=$VERIFY_TOKEN&hub.challenge=test123"

echo ""
echo ""
echo "⚠️  Make sure:"
echo "1. Django server is running"
echo "2. ngrok is running"  
echo "3. WHATSAPP_VERIFY_TOKEN in .env matches the token above"
echo ""



