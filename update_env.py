#!/usr/bin/env python3
"""Update .env file with new WhatsApp credentials"""

env_file = '/home/kali/Downloads/AirBnBSec/.env'

# Read current .env
with open(env_file, 'r') as f:
    content = f.read()

# Update WhatsApp configuration
lines = content.split('\n')
updated_lines = []

for line in lines:
    if line.startswith('WHATSAPP_ACCESS_TOKEN'):
        # Update with new token from curl
        updated_lines.append('WHATSAPP_ACCESS_TOKEN=EAAdG5fGlsf8BP9mRBYz2ZAFseEZBtlWdmzeOWfRP2OiRXygOZA1FZCim78uKXKepMuiFo1viQUOZCw4mZAmlXkby5XMElh0GlLjMNeHUBRZCdOj7N5x7G0mhQz6zxJpqFK9gq2mPfNJj4YnYQoeLkEywDgj5j9Cbu3XZBv9iEiZAkvLg1o3CjnI9R4pNTT2SDN6hHTTBToRZBpsr9a9uz6LkxClEOJmxGpvnUY2qJYX8MEMcT6KD04ZCMUeYZC2k6QZDZD')
    elif line.startswith('WHATSAPP_PHONE_NUMBER_ID'):
        updated_lines.append('WHATSAPP_PHONE_NUMBER_ID=104040046094231')
    elif line.startswith('WHATSAPP_VERIFY_TOKEN'):
        updated_lines.append('WHATSAPP_VERIFY_TOKEN=test123')
    elif line.startswith('# WhatsApp Configuration'):
        # Skip duplicate
        continue
    else:
        updated_lines.append(line)

# Add WhatsApp section if not exists
if '# WhatsApp Configuration' not in content:
    # Find where to insert
    insert_index = -1
    for i, line in enumerate(updated_lines):
        if line.startswith('WHATSAPP_ACCESS_TOKEN'):
            insert_index = i
            break
    
    if insert_index >= 0:
        updated_lines.insert(insert_index, '# WhatsApp Configuration')

# Write back
with open(env_file, 'w') as f:
    f.write('\n'.join(updated_lines))

print("✅ .env file updated successfully!")
print("\nUpdated values:")
print("  WHATSAPP_ACCESS_TOKEN=EAAdG5f...")
print("  WHATSAPP_PHONE_NUMBER_ID=104040046094231")
print("  WHATSAPP_VERIFY_TOKEN=test123")



