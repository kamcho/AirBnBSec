# Verification Implementation - User Intent Detection

## Overview

This implementation adds OpenAI-powered user intent detection and automatic verification handling to the AirBnBSec security incident management system.

## Features

### 1. **Automatic Verification Flow**
When a user wants to verify someone, the system:
- Detects the verification intent from natural language
- Extracts the ID number from the message
- Determines the user type (Citizen, Non-Citizen, Passport Holder, or KRA PIN)
- Automatically calls the appropriate verification function
- Returns structured verification results

### 2. **Supported Verification Types**
- **KRA PIN**: For business/company verification (fully implemented)
- **National ID**: For Kenyan citizens (structure ready, API integration pending)
- **Alien ID**: For non-citizens (structure ready, API integration pending)
- **Passport**: For passport holders (structure ready, API integration pending)

## Usage Examples

### Example 1: Basic Intent Detection
```python
from core.utils import detect_user_intent

result = detect_user_intent("I need to verify a client")
# Returns intent category, confidence, sentiment, urgency, etc.
```

### Example 2: Automatic Verification
```python
from core.utils import detect_user_intent

# The system automatically handles verification when intent is detected
result = detect_user_intent("verify Citizen > 629383933")
# Automatically extracts ID and user type, then calls verification
# Returns verification results in 'verification_result' field
```

### Example 3: Direct Verification
```python
from core.utils import handle_verification_intent

result = handle_verification_intent("verify KRA PIN > A123456789X")
# Directly processes verification without intent detection
# Returns verification results
```

## Supported Message Formats

### KRA PIN Verification
- `"verify KRA PIN > A123456789X"`
- `"I need to verify business with KRA PIN A123456789X"`
- `"check KRA PIN: A123456789X"`

### National ID Verification
- `"verify Citizen > 629383933"`
- `"verify National ID > 629383933"`
- `"I need to verify Kenyan citizen 629383933"`

### Alien ID Verification
- `"verify Non-Citizen > 123456789"`
- `"verify Alien ID > 123456789"`

### Passport Verification
- `"verify Passport Holder > A12345678"`
- `"verify Passport > A12345678"`

## Configuration

### Environment Variables Required

Add to your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

The system automatically loads this when making API calls.

### Settings Configuration

The following settings are added to `AirBnBSec/settings.py`:
```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')  # Default to GPT-4
```

## Function Reference

### `detect_user_intent(user_input, context=None)`
Detects user intent from input text using OpenAI.

**Parameters:**
- `user_input` (str): The user's message
- `context` (dict, optional): Additional context

**Returns:**
```python
{
    'success': bool,
    'intent_category': str,  # e.g., 'verify_client'
    'confidence': float,
    'sentiment': str,
    'urgency': str,
    'key_entities': list,
    'suggested_action': str,
    'reasoning': str,
    'verification_result': dict,  # Present if verification intent
    'message': str
}
```

### `handle_verification_intent(user_input)`
Directly handles verification by extracting ID and user type.

**Parameters:**
- `user_input` (str): Verification request message

**Returns:**
```python
{
    'success': bool,
    'user_type': str,  # 'kra_pin', 'national_id', 'alien_id', 'passport'
    'id_number': str,
    'data': dict,  # Verification data if successful
    'message': str
}
```

### `get_intent_recommendations(intent_category, urgency='medium')`
Get recommended actions based on detected intent.

**Parameters:**
- `intent_category` (str): The intent category
- `urgency` (str): The urgency level

**Returns:**
```python
{
    'priority': str,
    'actions': list,
    'next_step': str,
    'fields_needed': list
}
```

## Integration with KRA Verification

The verification system integrates with the existing KRA verification function:

```python
from core.utils import verify_kra_details

# Direct KRA verification (existing function)
result = verify_kra_details("A123456789X")
```

The new `handle_verification_intent` function automatically calls `verify_kra_details` when the user type is 'kra_pin'.

## Testing

Run the example file to see the system in action:

```bash
python core/intent_example.py
```

This will demonstrate:
- Intent detection
- Automatic verification for different document types
- KRA PIN verification
- Natural language processing

## Error Handling

The system gracefully handles:
- Missing OpenAI API key
- Invalid message formats
- API errors
- JSON parsing errors

All errors return structured error messages in the response.

## Files Modified

1. **`core/utils.py`**
   - Added `handle_verification_intent()` function
   - Enhanced `detect_user_intent()` to automatically handle verification
   - Added imports for OpenAI and JSON parsing

2. **`AirBnBSec/settings.py`**
   - Added `OPENAI_API_KEY` configuration
   - Added `OPENAI_MODEL` configuration

3. **`core/intent_example.py`**
   - Created example usage file
   - Demonstrates all verification flows

## Next Steps

To complete the implementation:

1. **Add API Key**: Add `OPENAI_API_KEY` to your `.env` file
2. **Test Verification**: Run `python core/intent_example.py`
3. **Integrate with Views**: Use these functions in your views to handle user input
4. **Add Other Document Types**: Implement APIs for National ID, Alien ID, and Passport verification if needed

## Notes

- The system currently only supports KRA PIN verification through the existing API
- National ID, Alien ID, and Passport verification return structured responses but require additional API integration
- All verification flows use GPT-4 for accuracy
- The system uses a low temperature (0.1-0.3) for consistent extraction results




