import requests
import logging

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token, bar_id=1):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.bar_id = bar_id
        self.user_id = None

    def _get_headers(self):
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
        except Exception:
            pass
        return None

    def validate_auth(self):
        return self._ensure_user_id() is not None

    def get_users(self):
        """Fetch all users (requires Admin/Super token)."""
        try:
            url = f"{self.base_url}/api/users"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch users: {e}")
        return []

    def get_shopping_list(self, target_user_id=None):
        """Fetch shopping list for specific user (or self if None)."""
        uid = target_user_id if target_user_id else self._ensure_user_id()
        if not uid: return []

        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch list for user {uid}: {e}")
        return []

    def remove_item_from_list(self, item_id, target_user_id=None):
        """Remove item from specific user's list."""
        uid = target_user_id if target_user_id else self._ensure_user_id()
        if not uid: return

        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list/{item_id}"
            requests.delete(url, headers=self._get_headers(), timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        """Fetch 'Cocktails I can make' (Shelf)."""
        uid = self._ensure_user_id()
        if not uid: return []
        try:
            url = f"{self.base_url}/api/users/{uid}/cocktails"
            params = {"per_page": 300} 
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception:
            pass
        return []

    def get_total_cocktails(self):
        """Fetch 'Total Cocktails' in the Bar Menu (Public)."""
        try:
            # Use the configured Bar ID to get the full menu
            url = f"{self.base_url}/api/bars/{self.bar_id}/cocktails"
            params = {"per_page": 300} 
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception:
            pass
        return []
