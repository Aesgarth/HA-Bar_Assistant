import requests
import logging

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    def validate_auth(self):
        """Test if the credentials are correct."""
        try:
            # Using /profile as a lightweight check (adjust endpoint if needed)
            response = requests.get(f"{self.base_url}/api/profile", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            _LOGGER.error(f"Error connecting to Bar Assistant: {e}")
            return False

    def get_shopping_list(self):
        """Fetch the shopping list."""
        try:
            response = requests.get(f"{self.base_url}/api/shopping-list", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch shopping list: {e}")
        return []

    def remove_item_from_list(self, item_id):
        """Remove an item from the Bar Assistant shopping list."""
        try:
            requests.delete(f"{self.base_url}/api/shopping-list/{item_id}", headers=self.headers, timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        """Fetch available cocktails."""
        try:
            # Assuming endpoint for cocktails user can make
            response = requests.get(f"{self.base_url}/api/cocktails?can_make=true", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
        return []
