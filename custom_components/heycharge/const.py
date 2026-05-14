"""Constants for the HeyCharge integration."""

DOMAIN = "heycharge"

# Configuration
CONF_HOST = "host"

# HTTP Basic auth — mirrors the firmware's local_api_handler.cpp.
# Username is hardcoded on the device; the password is collected from the
# user during config flow and may be left blank for older firmware that
# does not enforce auth. We deliberately do NOT pre-fill the firmware's
# factory default password here — users on auth-enforcing firmware should
# type whatever they actually set, and users on no-auth firmware leave it
# empty so we send no Authorization header at all.
LOCAL_API_USERNAME = "admin"

# Default values
DEFAULT_SCAN_INTERVAL = 5  # seconds

# API endpoints
API_STATUS = "/api/consumer_gateway/status"
API_CONFIG = "/api/consumer_gateway/config"
API_PAUSE = "/api/consumer_gateway/pause"
API_CURRENT_LIMIT = "/api/consumer_gateway/current_limit"
API_END_SESSION = "/api/consumer_gateway/end_session"
