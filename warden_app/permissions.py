import hashlib
import hmac
from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed

class HMACPermission(BasePermission):
    """
    Custom permission to verify HMAC signature.
    Expects 'X-Signature' header with the HMAC signature.
    The signature is computed over the request body using a shared secret key.
    """
    message = 'Invalid or missing HMAC signature.'

    def has_permission(self, request, view):
        if not settings.HMAC_SECRET_KEY:
            # If no secret key is configured, bypass HMAC check (useful for local dev/testing)
            # In a production environment, this should ideally raise an error or deny permission.
            # For this example, we'll allow if not set, but log a warning.
            # import logging
            # logging.warning("HMAC_SECRET_KEY is not set. HMAC verification is bypassed.")
            return True # Or False, depending on desired strictness

        signature_header = request.headers.get('X-Signature')
        if not signature_header:
            raise AuthenticationFailed('Missing X-Signature header.')

        try:
            # Ensure body is read and available for hashing
            # For DRF, request.data should be used if available and parsed,
            # otherwise request.body for raw byte string.
            # The content type matters here. For JSON, request.body is typically bytes.
            body = request.body
            if not isinstance(body, bytes):
                body = body.encode('utf-8') # Ensure it's bytes

            computed_signature = hmac.new(
                settings.HMAC_SECRET_KEY.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()

        except Exception as e:
            # import logging
            # logging.error(f"Error computing HMAC signature: {e}")
            raise AuthenticationFailed('Error processing request for HMAC verification.')

        if not hmac.compare_digest(computed_signature, signature_header):
            raise AuthenticationFailed('Invalid HMAC signature.')

        return True