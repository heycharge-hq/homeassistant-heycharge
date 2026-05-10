"""Constants for the HeyCharge integration."""

DOMAIN = "heycharge"

# Configuration
CONF_HOST = "host"

# HTTP Basic auth — mirrors the firmware's local_api_handler.cpp.
# Username is hardcoded on the device; password defaults to the firmware's
# DEFAULT_LOCAL_API_PASSWORD until the user provisions a custom one. Older
# firmware does not enforce auth at all and ignores the Authorization
# header, so sending the default credentials is safe everywhere.
LOCAL_API_USERNAME = "admin"
DEFAULT_LOCAL_API_PASSWORD = "heycharge"

# Default values
DEFAULT_SCAN_INTERVAL = 5  # seconds

# API endpoints
API_STATUS = "/api/consumer_gateway/status"
API_CONFIG = "/api/consumer_gateway/config"
API_PAUSE = "/api/consumer_gateway/pause"
API_CURRENT_LIMIT = "/api/consumer_gateway/current_limit"
API_START_SESSION = "/api/consumer_gateway/start_session"
API_END_SESSION = "/api/consumer_gateway/end_session"
