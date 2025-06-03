import hmac
import hashlib
import json

# This should be the EXACT same key as in your Django settings.py
HMAC_SECRET_KEY = 'your-super-secret-hmac-key-here' 

# This should be the EXACT JSON payload you send in Postman
payload = {
    "timestamp": "2023-10-27T10:00:00Z",
    "log_level": "ERROR",
    "message": "An unexpected error occurred service is down, session stopped",
    "source": "backend_service",
    "raw_log": "2023-10-27T10:00:00Z [ERROR] backend_service: An unexpected error occurred, session stopped"
}

# Convert payload to a compact JSON string (no extra whitespace)
json_string = json.dumps(payload, separators=(',', ':'))

# Generate HMAC signature
signature = hmac.new(
    HMAC_SECRET_KEY.encode('utf-8'),
    json_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"JSON String for signing: {json_string}")
print(f"Generated X-Signature: {signature}")