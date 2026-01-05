import requests
import logging

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.user_id = None

    def _get_user_id(self):
        """Fetch and cache the user ID from the profile."""
        if self.user_id:
            return self.user_id
            
        try:
            # We use /profile to get the current user's ID
            response = requests.get(f"{self.base_url}/api/profile", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                self.user_id = data.get('id')
                return self.user_id
            else:
                _LOGGER.error(f"Failed to fetch profile. Status: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error fetching user ID: {e}")
        return None

    def validate_auth(self):
        """Test if the credentials are correct."""
        return self._get_user_id() is not None

    def get_shopping_list(self):
        """Fetch the shopping list for the specific user."""
        uid = self._get_user_id()
        if not uid:
            return []

        try:
            # NEW ENDPOINT: /users/{id}/shopping-list
            url = f"{self.base_url}/api/users/{uid}/shopping-list"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                # API returns { data: [ ... ] }
                return response.json().get('data', [])
            elif response.status_code == 404:
                _LOGGER.error(f"Shopping list endpoint not found at {url}. Check API version.")
            else:
                _LOGGER.error(f"Shopping List Error {response.status_code}: {response.text}")

        except Exception as e:
            _LOGGER.error(f"Failed to fetch shopping list: {e}")
        return []

    def remove_item_from_list(self, item_id):
        """Remove an item from the Bar Assistant shopping list."""
        uid = self._get_user_id()
        if not uid:
            return

        try:
            # NEW ENDPOINT: /users/{id}/shopping-list/{item_id}
            url = f"{self.base_url}/api/users/{uid}/shopping-list/{item_id}"
            requests.delete(url, headers=self.headers, timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        """Fetch available cocktails."""
        try:
            # NEW FILTER FORMAT: ?filter[on_shelf]=true
            url = f"{self.base_url}/api/cocktails"
            params = {
                "include": "ingredients",
                "filter[on_shelf]": "true" 
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                _LOGGER.error(f"Cocktail Fetch Error {response.status_code}: {response.text}")
                
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
        return []
