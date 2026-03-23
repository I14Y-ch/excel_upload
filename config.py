import os

# I14Y API configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.i14y.admin.ch/api/partner/v1")

# Flask web application settings
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

if not FLASK_SECRET_KEY:
    raise ValueError("Missing FLASK_SECRET_KEY environment variable")

JWT_EXPECTED_ISSUER = os.environ.get("JWT_EXPECTED_ISSUER")
if not JWT_EXPECTED_ISSUER:
    raise ValueError("Missing JWT_EXPECTED_ISSUER environment variable")

MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16MB max file size by default
ALLOWED_EXTENSIONS = {"xlsx"}

# JWT configuration
JWT_DECODE_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_nbf": True,
    "verify_iat": True,
    "verify_aud": False,
    "verify_iss": bool(JWT_EXPECTED_ISSUER),
}
