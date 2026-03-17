"""Constants for the HeyCharge Gateway integration."""

DOMAIN = "heycharge_gateway"

# Configuration
CONF_HOST = "host"

# Default values
DEFAULT_SCAN_INTERVAL = 5  # seconds

# API endpoints
API_STATUS = "/api/consumer_gateway/status"
API_CONFIG = "/api/consumer_gateway/config"
API_PAUSE = "/api/consumer_gateway/pause"
API_CURRENT_LIMIT = "/api/consumer_gateway/current_limit"
API_START_SESSION = "/api/consumer_gateway/start_session"
API_END_SESSION = "/api/consumer_gateway/end_session"
