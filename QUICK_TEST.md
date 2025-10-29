# Quick Test Guide

## Your WhatsApp Credentials (from Meta Dashboard)
- **Phone Number ID**: `697849820089500`
- **Access Token**: (Already in .env)
- **API Version**: `v22.0`
- **Your Phone**: `254742134431`

## Test Options

### Option 1: Quick Send Test (Run This First!)
```bash
python test_send_message.py
```
This will send a test message to your WhatsApp number to verify credentials work.

### Option 2: Test via Webhook (Full Flow)
You need to:
1. **Set up ngrok** (for local testing):
```bash
# Install ngrok if you don't have it
# Download from https://ngrok.com/

# Start your Django server
python manage.py runserver

# In another terminal, expose it
ngrok http 8000
```

2. **Configure webhook in Meta Dashboard**:
   - Go to https://developers.facebook.com/
   - Your app → WhatsApp → Configuration
   - Set Webhook URL: `https://YOUR_NGROK_URL.ngrok.io/api/core/webhook/whatsapp/`
   - Set Verify Token: `your_custom_token_123`
   - Subscribe to `messages` field

3. **Add verify token to .env**:
```env
WHATSAPP_VERIFY_TOKEN=your_custom_token_123
```

4. **Send a WhatsApp message** to your business number!

### Option 3: Test Verification Directly
```python
# Run this in Django shell
python manage.py shell

from core.utils import handle_verification_intent
result = handle_verification_intent("verify KRA PIN > A123456789X")
print(result)
```

## What to Test

1. **Send regular message**: "Hi"
   - Should respond with available features

2. **Test verification**: "verify KRA PIN > A123456789X"
   - Should extract ID and verify via KRA API

3. **Test other intents**: "I need to report an incident"
   - Should detect intent and guide you

## Current Setup

✅ Phone Number ID: 697849820089500  
✅ API Version: v22.0  
✅ Access Token: In .env  
✅ OpenAI Key: Configured  

## Next Steps

1. Run `python test_send_message.py` to test credentials
2. Set up ngrok for local webhook testing
3. Configure webhook in Meta dashboard
4. Start sending WhatsApp messages!

## Troubleshooting

**If test fails**:
- Check access token is valid
- Verify phone number ID is correct
- Make sure recipient is registered/subscribed
- Check logs for errors

**If webhook not receiving**:
- Verify ngrok URL is accessible
- Check verify token matches
- Ensure HTTPS (ngrok provides this)
- Check Django server is running




