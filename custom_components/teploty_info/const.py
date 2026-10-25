"""Constants for the Teploty.info integration."""

from homeassistant.const import Platform

DOMAIN = "teploty_info"
API_URL = "https://teploty.info/ha_rest.php"
CONF_API_KEY = "api_key"
PLATFORMS = [Platform.SENSOR]
