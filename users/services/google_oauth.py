"""Google OAuth 2.0 token validation service."""
import requests
import logging
import time
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Token info endpoint for validating Google ID tokens
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def validate_google_id_token(id_token: str) -> dict | None:
    """
    Validate a Google ID token by calling Google's tokeninfo endpoint.

    Args:
        id_token: The JWT ID token from Google Sign-In

    Returns:
        dict: Token payload if valid, None if invalid

    Raises:
        ValueError: If token is invalid or client ID doesn't match
    """
    if not id_token:
        raise ValueError("ID token is required")

    try:
        # Call Google's tokeninfo endpoint to validate token
        response = requests.get(
            f"{GOOGLE_TOKENINFO_URL}?id_token={id_token}",
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()

        # Verify the token is intended for our app
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        if client_id and token_data.get('aud') != client_id:
            logger.warning(
                f"Token audience mismatch: expected {client_id}, "
                f"got {token_data.get('aud')}"
            )
            raise ValueError("Invalid token: audience mismatch")

        # Check issuer is Google
        if token_data.get('iss') not in (
            'accounts.google.com',
            'https://accounts.google.com'
        ):
            logger.warning(f"Invalid token issuer: {token_data.get('iss')}")
            raise ValueError("Invalid token: issuer not Google")

        # Check token is not expired (exp is Unix timestamp in seconds)
        # Google API returns exp as string, convert to float for comparison
        exp = token_data.get('exp', 0)
        try:
            exp = float(exp)
        except (ValueError, TypeError):
            logger.warning(f"Invalid exp format: {exp}")
            raise ValueError("Invalid token: malformed expiration")

        if exp < time.time():
            logger.warning("Token has expired")
            raise ValueError("Invalid token: expired")

        return token_data

    except requests.RequestException as e:
        logger.error(f"Failed to validate token with Google: {e}")
        raise ValueError(f"Failed to validate token: {str(e)}")


def extract_user_info(token_data: dict) -> dict:
    """
    Extract relevant user info from validated token data.

    Args:
        token_data: Validated token payload from Google

    Returns:
        dict with email, google_id, and picture (avatar)
    """
    return {
        'email': token_data.get('email', ''),
        'google_id': token_data.get('sub'),  # Google's unique user ID
        'picture': token_data.get('picture', ''),
        'email_verified': token_data.get('email_verified', False),
    }
