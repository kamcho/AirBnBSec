# WhatsApp Integration Setup Guide

## Overview

This implementation integrates Meta's Official WhatsApp Business API with your AirBnBSec security incident management system. Users can:

- Send messages to your WhatsApp Business number
- Automatically detect their intent (verification, incident reporting, etc.)
- Get immediate responses with verification results
- Complete verification workflow entirely via WhatsApp

## Features

### ✅ Automatic Intent Detection
- Uses OpenAI to understand natural language
- Detects verification, incident reporting, and other intents
- No rigid command structure required

### ✅ Automatic Verification
- Extracts ID number and document type from user's message
- Calls KRA API automatically
- Returns formatted verification results
- Supports multiple document types

### ✅ Real-time Responses
- Instant feedback to users
- Formatted messages with emojis
- Clear error messages
- Helpful suggestions

## Setup Instructions

### 1. Get WhatsApp Business API Credentials

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create or select your app
3. Add "WhatsApp" product to your app
4. Set up a Meta WhatsApp Business Account
5. Get your credentials:

**Required Credentials:**
- `WHATSAPP_ACCESS_TOKEN` - Permanent or temporary access token
- `WHATSAPP_PHONE_NUMBER_ID` - Your WhatsApp Business phone number ID
- `WHATSAPP_BUSINESS_ACCOUNT_ID` - Your Business Account ID
- `WHATSAPP_VERIFY_TOKEN` - A token of your choice for webhook verification

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_123

# KRA API Configuration
GAVACONNECT_API_KEY=your_gavaconnect_api_key
GAVACONNECT_API_SECRET=your_gavaconnect_api_secret
```

### 3. Configure Webhook in Meta Dashboard

1. Go to your app's WhatsApp settings
2. Navigate to "Configuration" tab
3. Click "Edit" next to "Webhook"
4. Set your callback URL:
   ```
   https://yourdomain.com/api/core/webhook/whatsapp/
   ```
5. Set verify token to match your `WHATSAPP_VERIFY_TOKEN`
6. Subscribe to `messages` field
7. Click "Verify and Save"

### 4. Test the Integration

#### Test Webhook Verification
```bash
curl -X GET "https://yourdomain.com/api/core/webhook/whatsapp/?hub.mode=subscribe&hub.verify_token=your_custom_verify_token_123&hub.challenge=test_challenge"
```

Expected response: `test_challenge`

#### Test Sending a Message (Optional)
```bash
curl -X POST "https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "254712345678",
    "type": "text",
    "text": { "body": "Hello from WhatsApp!" }
  }'
```

## Usage Examples

### Example 1: Verify a KRA PIN

**User sends:**
```
verify KRA PIN > A123456789X
```

**System response:**
```
✅ Verification Successful

📋 User Type: Kra Pin
🆔 ID Number: A123456789X
👤 Verified Name: John Doe Enterprises
🆔 KRA PIN: A123456789X

✨ Verification completed successfully!
```

### Example 2: Verify a National ID

**User sends:**
```
verify Citizen > 629383933
```

**System response:**
```
⚠️ Verification Pending

📋 User Type: National Id
🆔 ID Number: 629383933

❌ Verification for national_id (ID: 629383933) is not yet implemented. Currently, only KRA PIN verification is fully supported.

💡 Currently, only KRA PIN verification is fully supported.
```

### Example 3: Report an Incident

**User sends:**
```
I need to report a suspicious person near the entrance
```

**System response:**
```
🔔 Reporting Incident

To report a security incident, please provide:
• Type of incident
• Location and time
• Description of what happened
• Any evidence (photos/videos)

I'll help guide you through the process.
```

### Example 4: Ask a Question

**User sends:**
```
What can you do?
```

**System response:**
```
💬 How Can I Help?

Available features:
• Verify clients/guests 📋
• Report incidents 🚨
• Add evidence 📎
• View incidents 📊

Just describe what you need!
```

## Message Flow

```
User WhatsApp Message
         ↓
    Webhook receives
         ↓
   Detect Intent (OpenAI)
         ↓
   Is Verification?
         ↓ (Yes)
   Extract ID & Type (OpenAI)
         ↓
   Call KRA API
         ↓
   Format Response
         ↓
   Send via WhatsApp API
```

## Supported Message Formats

### Verification
- `verify KRA PIN > A123456789X`
- `verify Citizen > 629383933`
- `verify Non-Citizen > 123456789`
- `verify Passport Holder > A12345678`
- `I need to verify business KRA PIN A123456789X`
- `check KRA PIN: A123456789X`

### Incident Reporting
- `I need to report an incident`
- `report suspicious activity`
- `there's a security issue`

### Viewing
- `show me incidents`
- `view all reports`
- `list security incidents`

## API Endpoints

### Webhook Endpoint
```
GET/POST: /api/core/webhook/whatsapp/
```

**GET** - Webhook verification
**POST** - Receive messages

## Implementation Details

### Files Created/Modified

1. **`core/whatsapp.py`** - WhatsApp integration logic
   - `whatsapp_webhook()` - Handles webhook requests
   - `send_whatsapp_message()` - Sends messages
   - `send_whatsapp_template()` - Sends template messages
   - `process_whatsapp_message()` - Processes incoming messages
   - `send_verification_response()` - Sends verification results

2. **`core/urls.py`** - Added webhook route
   - `path('webhook/whatsapp/', ...)`

3. **`core/views.py`** - Imported webhook handler

4. **`AirBnBSec/settings.py`** - Added WhatsApp configuration

## Error Handling

The system handles:
- Missing API credentials
- Invalid webhook requests
- Failed message sending
- OpenAI API errors
- KRA API errors
- JSON parsing errors

All errors are logged and return appropriate error messages to users.

## Security Considerations

1. **Webhook Verification**: Uses HMAC signature verification (Meta recommended)
2. **CSRF Exempt**: Webhook endpoint is CSRF exempt (external API)
3. **Environment Variables**: All sensitive data stored in `.env`
4. **HTTPS Required**: Webhook must use HTTPS in production

## Troubleshooting

### Webhook Not Receiving Messages
1. Check if webhook URL is accessible
2. Verify token matches in Meta dashboard
3. Check logs for incoming requests

### Messages Not Sending
1. Verify `WHATSAPP_ACCESS_TOKEN` is valid
2. Check `WHATSAPP_PHONE_NUMBER_ID` is correct
3. Verify recipient is subscribed (for template messages)

### Verification Not Working
1. Check OpenAI API key is set
2. Verify KRA API credentials
3. Check logs for extraction errors

## Testing with ngrok (Development)

For local development, use ngrok to expose your local server:

```bash
# Install ngrok
# Download from https://ngrok.com/

# Expose local server
ngrok http 8000

# Use the HTTPS URL in Meta webhook configuration
# Example: https://abc123.ngrok.io/api/core/webhook/whatsapp/
```

## Production Deployment

1. **HTTPS Required**: Use proper SSL certificate
2. **Environment Variables**: Ensure all are set in production
3. **Webhook URL**: Update in Meta dashboard
4. **Token Security**: Use strong, random verify token
5. **Rate Limiting**: Consider adding rate limiting
6. **Logging**: Monitor logs for errors

## Next Steps

1. Add support for image/file uploads (evidence)
2. Implement National ID verification API
3. Add conversation context/memory
4. Implement multi-step verification flows
5. Add admin dashboard for viewing conversations
6. Integrate with incident creation workflow

## Support

For issues or questions:
- Check logs in Django console
- Verify environment variables
- Test with curl commands
- Review Meta API documentation

## API Rate Limits

**WhatsApp Business API:**
- Free tier: 1,000 conversations per month
- Each 24-hour session counts as 1 conversation
- Rate limits apply to API calls

**OpenAI API:**
- Usage-based billing
- Consider caching for production

## Message Templates

To send official template messages, register them in Meta dashboard:

1. Go to WhatsApp > Message Templates
2. Create template
3. Get approved by Meta
4. Use `send_whatsapp_template()` function




