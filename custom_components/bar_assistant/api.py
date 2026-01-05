import requests
import logging

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        
        # RESTORED: Default to Bar ID 1. 
        # This fixes the "Chicken and Egg" problem where we need an ID to query the API.
        self.bar_id = 1 
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Bar-Assistant-Bar-Id": str(self.bar_id)
        }
        self.user_id = None

    def _ensure_user_id(self):
        """Ensure we have the User ID."""
        if self.user_id:
            return self.user_id
            
        try:
            url = f"{self.base_url}/api/profile"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                self.user_id = data.get('id')
                return self.user_id
        except Exception as e:
            _LOGGER.error(f"Error connecting to Bar Assistant profile: {e}")
        return None

    def _update_bar_id_if_needed(self):
        """Try to find the correct bar ID, but fall back to 1 if it fails."""
        try:
            url = f"{self.base_url}/api/bars"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    # If we found a bar and it's different from our default, update it.
                    found_id = data[0]['id']
                    if found_id != self.bar_id:
                        self.bar_id = found_id
                        self.headers["Bar-Assistant-Bar-Id"] = str(self.bar_id)
                        _LOGGER.info(f"Updated Bar ID to {self.bar_id}")
        except Exception:
            # If this fails, we just silently keep using ID 1, which works for 99% of users.
            pass

    def validate_auth(self):
        # We try to update the bar ID, then check the user
        self._update_bar_id_if_needed()
        return self._ensure_user_id() is not None

    def get_shopping_list(self):
        self._ensure_user_id()
        if not self.user_id: return []

        try:
            url = f"{self.base_url}/api/users/{self.user_id}/shopping-list"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                _LOGGER.error(f"Shopping List Error {response.status_code}: {response.text}")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch shopping list: {e}")
        return []

    def remove_item_from_list(self, item_id):
        self._ensure_user_id()
        if not self.user_id: return

        try:
            url = f"{self.base_url}/api/users/{self.user_id}/shopping-list/{item_id}"
            requests.delete(url, headers=self.headers, timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        self._ensure_user_id()
        if not self.user_id: return []

        try:
            url = f"{self.base_url}/api/users/{self.user_id}/cocktails"
            params = {"per_page": 300} 
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                _LOGGER.error(f"Cocktail Fetch Error {response.status_code}: {response.text}")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
        return []
