# Step-by-Step WhatsApp Echo Setup

## What You Need

✅ **Your .env file** should have:
```env
WHATSAPP_ACCESS_TOKEN=EAAdG5fGlsf8BP9mRBYz2ZAFseEZBtlWdmzeOWfRP2OiRXygOZA1FZCim78uKXKepMuiFo1viQUOZCw4mZAmlXkby5XMElh0GlLjMNeHUBRZCdOj7N5x7G0mhQz6zxJpqFK9gq2mPfNJj4YnYQoeLkEywDgj5j9Cbu3XZBv9iEiZAkvLg1o3CjnI9R4pNTT2SDN6hHTTBToRZBpsr9a9uz6LkxClEOJmxGpvnUY2qJYX8MEMcT6KD04ZCMUeYZC2k6QZDZD
WHATSAPP_PHONE_NUMBER_ID=104040046094231
WHATSAPP_VERIFY_TOKEN=test123
```

## Steps to Get WhatsApp Echo Working

### STEP 1: Start Django Server
```bash
python manage.py runserver
```
Keep this running in terminal 1.

### STEP 2: Start ngrok
In a new terminal:
```bash
ngrok http 8000
```
You'll see a URL like: `https://abc123.ngrok-free.dev`

### STEP 3: Configure Webhook in Meta Dashboard
1. Go to https://developers.facebook.com/
2. Your app → WhatsApp → Configuration
3. Click "Edit" next to Webhook
4. Enter:
   - **Callback URL**: `https://YOUR_NGROK_URL.ngrok-free.dev/api/core/webhook/whatsapp/`
   - **Verify Token**: `test123`
5. Click "Verify and Save"
6. Subscribe to `messages` field
7. Click "Save"

### STEP 4: Test!
Send a WhatsApp message to your business number.

**Expected:**
- Your message appears in Django console
- You receive back: "Echo: [your message]"

## What Happens

1. ✅ User sends WhatsApp message
2. ✅ Meta sends to your ngrok URL
3. ✅ Django receives at `/api/core/webhook/whatsapp/`
4. ✅ Code extracts message and sender
5. ✅ Code sends echo back via WhatsApp API
6. ✅ User receives echo message

## Debug Info

You'll see in Django console:
```
======================================================================
🔔 MESSAGE RECEIVED
======================================================================
{full webhook JSON}
📨 From: 254742134431
📨 Message: hello
📤 Sending to 254742134431: Echo: hello
📥 Status: 200
✅ Echo sent!
```

## Troubleshooting

**400 Bad Request:**
- Check verify token matches (test123)
- Check webhook URL is correct

**Not receiving messages:**
- Make sure ngrok is running
- Check ngrok URL in Meta dashboard
- Verify Django server is running

**Can't send messages:**
- Check access token is valid
- Check phone number ID is correct
- Make sure recipient phone is formatted correctly (254...)

## Next Steps

Once echo works, we'll add:
- Intent detection with OpenAI
- Verification handler
- Smart responses



