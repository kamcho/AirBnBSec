# AirBnBSec Integration Overview

## Complete System Architecture

Your AirBnBSec system now has three integrated components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                        │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   WhatsApp   │  │   Web App    │  │   API/JSON   │           │
│  │   Messages   │  │   Interface  │  │   Endpoints  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
└─────────┼─────────────────┼─────────────────┼────────────────────┘
          │                 │                 │
          │                 │                 │
┌─────────┼─────────────────┼─────────────────┼────────────────────┐
│         │                 │                 │                      │
│  ┌──────▼─────────────────▼─────────────────▼───────┐             │
│  │        AI-POWERED INTENT DETECTION              │             │
│  │          (OpenAI GPT-4)                          │             │
│  └──────────────┬──────────────────────────────────┘             │
│                 │                                                 │
│  ┌──────────────▼──────────────────────────────────┐             │
│  │              INTENT PROCESSOR                    │             │
│  │  • Detect user intent                           │             │
│  │  • Extract information                           │             │
│  │  • Route to appropriate handler                  │             │
│  └──────────────┬──────────────────────────────────┘             │
│                 │                                                 │
│  ┌──────────────▼──────────────────────────────────┐             │
│  │           VERIFICATION SYSTEM                   │             │
│  │  • KRA PIN (Fully Implemented)                  │             │
│  │  • National ID (Structure Ready)                │             │
│  │  • Alien ID (Structure Ready)                   │             │
│  │  • Passport (Structure Ready)                   │             │
│  └──────────────┬──────────────────────────────────┘             │
│                 │                                                 │
│  ┌──────────────▼──────────────────────────────────┐             │
│  │              KRA API INTEGRATION                 │             │
│  │              (GavaConnect API)                   │             │
│  └─────────────────────────────────────────────────┘             │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Features Overview

### 1. AI-Powered Intent Detection ✅
- **Location**: `core/utils.py` - `detect_user_intent()`
- **Technology**: OpenAI GPT-4
- **Capabilities**:
  - Understands natural language
  - Detects verification, reporting, viewing intents
  - Extracts sentiment and urgency
  - Suggests appropriate actions

### 2. Verification Handler ✅
- **Location**: `core/utils.py` - `handle_verification_intent()`
- **Technology**: OpenAI + KRA API
- **Capabilities**:
  - Extracts ID numbers from messages
  - Identifies document type (KRA PIN, National ID, etc.)
  - Calls appropriate verification API
  - Returns structured results

### 3. WhatsApp Integration ✅
- **Location**: `core/whatsapp.py`
- **Technology**: Meta Official WhatsApp Business API
- **Capabilities**:
  - Receives messages via webhook
  - Processes for intent automatically
  - Handles verification workflow
  - Sends formatted responses
  - Real-time communication

### 4. KRA Verification ✅
- **Location**: `core/utils.py` - `verify_kra_details()`
- **Technology**: GavaConnect API
- **Capabilities**:
  - Verifies KRA PIN
  - Returns taxpayer information
  - Handles errors gracefully

## File Structure

```
AirBnBSec/
├── core/
│   ├── __init__.py
│   ├── urls.py              # URL routing including webhook
│   ├── views.py             # API views
│   ├── utils.py             # Intent detection & verification
│   ├── whatsapp.py          # WhatsApp integration
│   ├── intent_example.py    # Usage examples
│   └── test_whatsapp.py     # Test script
│
├── AirBnBSec/
│   ├── settings.py          # All configurations
│   └── urls.py              # Main URL patterns
│
├── VERIFICATION_IMPLEMENTATION.md    # Verification docs
├── WHATSAPP_SETUP.md                # WhatsApp setup guide
└── INTEGRATION_OVERVIEW.md           # This file
```

## API Endpoints

### Core Endpoints
- `GET /api/core/webhook/whatsapp/` - Webhook verification
- `POST /api/core/webhook/whatsapp/` - Receive WhatsApp messages
- `POST /api/core/verify-kra/` - Direct KRA verification API

### Home Endpoints
- `/` - Incident dashboard
- `/incidents/create/` - Create incident
- `/incidents/<id>/` - Incident details
- `/clients/verify/` - Client verification form

## Environment Variables Required

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=EAAx...
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_BUSINESS_ACCOUNT_ID=987654321
WHATSAPP_VERIFY_TOKEN=my_secret_token

# KRA/GavaConnect Configuration
GAVACONNECT_API_KEY=your_key
GAVACONNECT_API_SECRET=your_secret
```

## Quick Start Guide

### 1. Setup Environment
```bash
# Add all required environment variables to .env
cp .env.example .env
# Edit .env with your credentials
```

### 2. Install Dependencies
```bash
pip install openai django python-dotenv requests
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Test Locally
```bash
# Test intent detection
python core/intent_example.py

# Test WhatsApp flow
python core/test_whatsapp.py
```

### 5. Configure WhatsApp Webhook
- Go to Meta Developers Dashboard
- Configure webhook: `https://yourdomain.com/api/core/webhook/whatsapp/`
- Set verify token to match `WHATSAPP_VERIFY_TOKEN`

### 6. Deploy
- Use HTTPS (required for webhook)
- Set environment variables in production
- Test with real WhatsApp messages

## Usage Examples

### Example 1: WhatsApp Verification

**User sends via WhatsApp:**
```
verify KRA PIN > A123456789X
```

**Flow:**
1. Webhook receives message
2. `detect_user_intent()` identifies verification intent
3. `handle_verification_intent()` extracts ID and type
4. `verify_kra_details()` calls KRA API
5. Response formatted and sent via WhatsApp

**User receives:**
```
✅ Verification Successful

📋 User Type: Kra Pin
🆔 ID Number: A123456789X
👤 Verified Name: John Enterprises
🆔 KRA PIN: A123456789X

✨ Verification completed successfully!
```

### Example 2: Python Code

```python
from core.utils import detect_user_intent

# Detect intent from user message
result = detect_user_intent("I need to verify a client")

# Check intent category
if result['intent_category'] == 'verify_client':
    # Access verification results
    verification = result['verification_result']
    print(f"Success: {verification['success']}")
    print(f"User Type: {verification['user_type']}")
    print(f"ID Number: {verification['id_number']}")
```

### Example 3: Direct Verification

```python
from core.utils import handle_verification_intent

# Directly handle verification
result = handle_verification_intent("verify Citizen > 629383933")

print(f"User Type: {result['user_type']}")
print(f"ID Number: {result['id_number']}")
print(f"Message: {result['message']}")
```

## Supported Intent Categories

1. **verify_client** - Verify a person/business identity
2. **report_incident** - Report a security incident
3. **view_incidents** - View existing incidents
4. **add_evidence** - Add evidence to an incident
5. **update_incident** - Update incident status
6. **get_analytics** - Get statistics/analytics
7. **ask_question** - General questions
8. **other** - Doesn't fit any category

## Testing

### Run Tests Locally

```bash
# Test intent detection
python core/intent_example.py

# Test WhatsApp integration
python core/test_whatsapp.py

# Run Django tests
python manage.py test
```

### Test Webhook (Development)

Use ngrok for local testing:

```bash
# Start ngrok
ngrok http 8000

# Use HTTPS URL in Meta dashboard:
# https://abc123.ngrok.io/api/core/webhook/whatsapp/
```

### Test with Real WhatsApp

1. Configure webhook in Meta dashboard
2. Send message to your Business number
3. Check logs for processing
4. Verify response received

## Monitoring & Logging

### Console Logs
- Intent detection results
- Verification status
- API errors
- WhatsApp webhook activity

### Debug Information
Set `DEBUG=True` in settings for detailed logs

### Production Logging
Configure Django logging for production:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'whatsapp_webhook.log',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## Security Best Practices

1. ✅ CSRF exempt for webhook (external API)
2. ✅ Environment variables for sensitive data
3. ✅ HTTPS required for webhooks
4. ✅ Verify token validation
5. ⚠️ Consider rate limiting
6. ⚠️ Add request signing verification (HMAC)

## Next Steps / Roadmap

### Completed ✅
- Intent detection with OpenAI
- KRA PIN verification
- WhatsApp integration
- Automatic verification workflow
- Error handling

### To Implement ⏳
- [ ] National ID verification API
- [ ] Alien ID verification API  
- [ ] Passport verification API
- [ ] Image/file upload support
- [ ] Conversation context/memory
- [ ] Multi-step verification flows
- [ ] Admin dashboard for conversations
- [ ] Incident creation via WhatsApp
- [ ] Evidence upload via WhatsApp
- [ ] Automated notifications
- [ ] Analytics and reporting

## Support

### Common Issues

**Webhook not receiving messages:**
- Check HTTPS is enabled
- Verify token matches
- Check webhook status in Meta dashboard

**Verification not working:**
- Check OpenAI API key
- Verify KRA credentials
- Check logs for errors

**Messages not sending:**
- Verify WhatsApp token
- Check phone number ID
- Ensure recipient is subscribed

### Get Help
- Check individual documentation files
- Review code comments
- Test with provided examples
- Check Django logs

## License & Credits

- Django Framework
- OpenAI API
- Meta WhatsApp Business API
- GavaConnect API




