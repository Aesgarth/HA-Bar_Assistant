import logging
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class BarAssistantAPI:
    def __init__(self, base_url, token, bar_id=1):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.bar_id = bar_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Bar-Assistant-Bar-Id": str(self.bar_id),
        }

    async def _request(self, method, endpoint, **kwargs):
        """Internal method to handle requests."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.request(
                        method, url, headers=self.headers, **kwargs
                    ) as response:
                        if response.status in (200, 201, 204):
                            if method == "DELETE" or response.status == 204:
                                return True
                            return await response.json()
                        else:
                            _LOGGER.error(
                                f"Error {response.status} connecting to {url}"
                            )
                            return None
        except Exception as e:
            _LOGGER.error(f"Connection error to {url}: {e}")
            return None

    def validate_auth(self):
        """Synchronous validation for config flow."""
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/profile", headers=self.headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def get_users(self):
        """Synchronous user fetch for config flow."""
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/users", headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return []
        except Exception:
            return []

    async def async_get_profile(self):
        """Get current user profile."""
        return await self._request("GET", "/api/profile")

    async def async_get_shopping_list(self, user_id):
        """Fetch the shopping list for a specific user."""
        data = await self._request("GET", f"/api/users/{user_id}/shopping-list")
        return data.get("data", []) if data else []

    async def async_add_to_list(self, user_id, ingredient_id):
        """Add an item back to the shopping list."""
        # Assuming standard POST payload for adding items
        payload = {"ingredient_id": int(ingredient_id), "quantity": 1}
        return await self._request(
            "POST", 
            f"/api/users/{user_id}/shopping-list", 
            json=payload
        )

    async def async_remove_from_list(self, user_id, ingredient_ids):
        """Batch delete items from the shopping list."""
        if not ingredient_ids:
            return True
        
        payload = {"ingredients": [{"id": i_id} for i_id in ingredient_ids]}
        return await self._request(
            "POST", 
            f"/api/users/{user_id}/shopping-list/batch-delete", 
            json=payload
        )

    async def async_get_cocktails(self, user_id):
        """Get cocktails the user can make (Shelf)."""
        data = await self._request("GET", f"/api/users/{user_id}/cocktails")
        return data.get("data", []) if data else []

    async def async_get_total_cocktails(self):
        """Get total cocktails in the bar (Menu)."""
        data = await self._request("GET", f"/api/bars/{self.bar_id}/cocktails")
        return data.get("data", []) if data else []
