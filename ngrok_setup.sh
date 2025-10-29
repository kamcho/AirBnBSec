#!/bin/bash

# Ngrok Webhook Setup Guide
# This script helps you test the webhook

echo "=========================================="
echo "WHATSAPP WEBHOOK SETUP"
echo "=========================================="
echo ""

echo "STEP 1: Start Django Server"
echo "Run in terminal 1:"
echo "  python manage.py runserver"
echo ""

echo "STEP 2: Start ngrok"
echo "Run in terminal 2:"
echo "  ngrok http 8000"
echo ""

echo "STEP 3: Copy your ngrok URL"
echo "  You'll see something like: https://abc123.ngrok.io"
echo ""

echo "STEP 4: Test webhook verification"
echo "Replace YOUR_NGROK_URL with your actual ngrok URL:"
echo ""

VERIFY_TOKEN="my_whatsapp_token_123"
echo "curl \"https://YOUR_NGROK_URL.ngrok.io/api/core/webhook/whatsapp/?hub.mode=subscribe&hub.verify_token=$VERIFY_TOKEN&hub.challenge=test123\""
echo ""

echo "STEP 5: Configure in Meta Dashboard"
echo "  URL: https://YOUR_NGROK_URL.ngrok.io/api/core/webhook/whatsapp/"
echo "  Verify Token: $VERIFY_TOKEN"
echo "  Subscribe to: messages"
echo ""

echo "STEP 6: Update .env with verify token"
echo "  Add: WHATSAPP_VERIFY_TOKEN=$VERIFY_TOKEN"
echo ""

echo "=========================================="



