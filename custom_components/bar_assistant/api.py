import requests
import logging
from requests.exceptions import JSONDecodeError

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Bar-Assistant-Bar-Id": "1"
        }
        self.user_id = None

    def _handle_response(self, response, source="API"):
        """Helper to safely parse JSON or log the error."""
        if response.status_code == 200:
            try:
                return response.json().get('data', [])
            except JSONDecodeError:
                # This is the key debug line
                _LOGGER.error(f"{source} returned 200 OK but content is not JSON.")
                _LOGGER.error(f"Response start: {response.text[:200]}") # Log first 200 chars
                return []
        else:
            _LOGGER.error(f"{source} failed with {response.status_code}: {response.text[:200]}")
            return []

    def _get_user_id(self):
        if self.user_id:
            return self.user_id
            
        try:
            url = f"{self.base_url}/api/users"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # Manual check for users endpoint as it returns a list, not always wrapped the same way
            if response.status_code == 200:
                try:
                    data = response.json().get('data', [])
                    if data:
                        self.user_id = data[0]['id']
                        return self.user_id
                except JSONDecodeError:
                    _LOGGER.error(f"Get User ID returned HTML instead of JSON: {response.text[:100]}")
            else:
                _LOGGER.error(f"Failed to get users. Status: {response.status_code}")
                
        except Exception as e:
            _LOGGER.error(f"Error fetching user ID: {e}")
        return None

    def validate_auth(self):
        return self._get_user_id() is not None

    def get_shopping_list(self):
        uid = self._get_user_id()
        if not uid: return []
        
        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list"
            response = requests.get(url, headers=self.headers, timeout=10)
            return self._handle_response(response, "Shopping List")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch shopping list: {e}")
            return []

    def remove_item_from_list(self, item_id):
        uid = self._get_user_id()
        if not uid: return

        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list/{item_id}"
            requests.delete(url, headers=self.headers, timeout=10)
        except Exception as e:
            _LOGGER.error(f"Failed to delete item {item_id}: {e}")

    def get_cocktails(self):
        uid = self._get_user_id()
        if not uid: return []

        try:
            url = f"{self.base_url}/api/users/{uid}/cocktails"
            params = {"per_page": 50} 
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            return self._handle_response(response, "Cocktails")
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
            return []
