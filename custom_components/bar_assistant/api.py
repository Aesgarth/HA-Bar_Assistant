import requests
import logging

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

    def _get_user_id(self):
        """Fetch the User ID with heavy debugging."""
        if self.user_id:
            return self.user_id
            
        try:
            url = f"{self.base_url}/api/users"
            _LOGGER.info(f"Attempting to connect to: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # --- DEBUGGING BLOCK ---
            content_type = response.headers.get('Content-Type', '')
            raw_text = response.text
            
            _LOGGER.info(f"Response Status: {response.status_code}")
            _LOGGER.info(f"Response Content-Type: {content_type}")
            _LOGGER.info(f"Raw Response Start: {raw_text[:200]}") # Logs the first 200 chars
            
            if response.status_code == 200:
                if "<!DOCTYPE" in raw_text or "<html" in raw_text:
                    _LOGGER.error("CRITICAL ERROR: The API URL is pointing to a website, not the API. Check your port!")
                    return None
                
                try:
                    data = response.json().get('data', [])
                    if data:
                        self.user_id = data[0]['id']
                        _LOGGER.info(f"Success! Found User ID: {self.user_id}")
                        return self.user_id
                except Exception as json_err:
                    _LOGGER.error(f"JSON Parsing failed: {json_err}")
            else:
                _LOGGER.error(f"Failed to get users. Status: {response.status_code}")
                
        except Exception as e:
            _LOGGER.error(f"Connection Error: {e}")
        return None

    def validate_auth(self):
        return self._get_user_id() is not None

    def get_shopping_list(self):
        uid = self._get_user_id()
        if not uid: return []

        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch list: {e}")
        return []

    def remove_item_from_list(self, item_id):
        uid = self._get_user_id()
        if not uid: return
        try:
            url = f"{self.base_url}/api/users/{uid}/shopping-list/{item_id}"
            requests.delete(url, headers=self.headers, timeout=10)
        except Exception:
            pass

    def get_cocktails(self):
        uid = self._get_user_id()
        if not uid: return []
        try:
            url = f"{self.base_url}/api/users/{uid}/cocktails"
            params = {"per_page": 50} 
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            _LOGGER.error(f"Failed to fetch cocktails: {e}")
            return []
