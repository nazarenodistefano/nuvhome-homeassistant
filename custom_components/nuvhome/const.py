"""Costanti dell'integrazione NuvHome."""

from datetime import timedelta

DOMAIN = "nuvhome"
DEFAULT_BASE_URL = "https://nuvhome.it"
SUMMARY_PATH = "/api/integrations/home-assistant/summary"
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
UPDATE_INTERVAL = timedelta(minutes=30)
REQUEST_TIMEOUT = 30
