import requests
import logging

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token, bar_id=1):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.bar_id = bar_id # Saved from Config
        self.user_id = None

    def _get_headers(self):
        """Construct headers dynamically with the Configured Bar ID."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Bar-Assistant-Bar-Id": str(self.bar_id)
        }

    def _ensure_user_id(self):
        if self.user_id: return self.user_id
        try:
            url = f"{self.base_url}/api/profile"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                self.user_id = data.get('id')
                return self.user_id
            else:
                _LOGGER.error(f"Profile error {response.status_code}: {response.text}")
        except Exception as e:
            _LOGGER.error(f"Error connecting to profile: {e}")
        return None

    def validate_auth(self):
        return self._ensure_user_id() is not None

    def get_shopping_list(self):
        self._ensure_user_id()
        if not self.user_id: return []
        try:
            url = f"{self.base_url}/api/users/{self.user_id}/shopping-list"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                _LOGGER.error(f"Shopping List Error {response.status_code}: {response.text}")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch list: {e}")
        return []

    def remove_item_from_list(self, item_id):
        self._ensure_user_id()
        if not self.user_id: return
        try:
            url = f"{self.base_url}/api/users/{self.user_id}/shopping-list/{item_id}"
            requests.delete(url, headers=self._get_headers(), timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        self._ensure_user_id()
        if not self.user_id: return []
        try:
            url = f"{self.base_url}/api/users/{self.user_id}/cocktails"
            params = {"per_page": 300} 
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                _LOGGER.error(f"Cocktail Error {response.status_code}: {response.text}")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
        return []
