import os

# I14Y API configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.i14y.admin.ch/api/partner/v1")

# Flask web application settings
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "development-only-key")  # Only use default for local development
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16MB max file size by default
ALLOWED_EXTENSIONS = {'xlsx'}

# JWT configuration
JWT_DECODE_OPTIONS = {
    "verify_signature": False,
    "verify_exp": True,
    "verify_nbf": True,
    "verify_iat": True,
    "verify_aud": False
}