import logging
import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID, CONF_SYNC_USER_IDS, DEFAULT_BAR_ID
from .api import BarAssistantAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "todo"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config_data = entry.data
    
    base_url = config_data.get(CONF_API_URL, "").rstrip("/")
    token = config_data.get(CONF_API_TOKEN, "")
    bar_id = config_data.get(CONF_BAR_ID, DEFAULT_BAR_ID)
    selected_user_ids = config_data.get(CONF_SYNC_USER_IDS, [])

    # Legacy fallback
    if not base_url:
        base_url = config_data.get("url", "").rstrip("/")
    if not token:
        token = config_data.get("token", "")

    # Init API
    hass.data.setdefault(DOMAIN, {})
    api_client = BarAssistantAPI(base_url, token, bar_id)
    hass.data[DOMAIN][entry.entry_id] = api_client

    # Load Platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ------------------------------------------------------------------
    # Service: Sync Shopping List (Legacy / Automation Support)
    # ------------------------------------------------------------------
    async def async_handle_sync(call: ServiceCall):
        _LOGGER.info("!!! BAR ASSISTANT SYNC SERVICE STARTED !!!")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Bar-Assistant-Bar-Id": str(bar_id),
        }

        async with aiohttp.ClientSession() as session:
            try:
                users_to_sync = selected_user_ids
                
                # Fallback to Profile User
                if not users_to_sync:
                    async with session.get(f"{base_url}/api/profile", headers=headers) as resp:
                        if resp.status == 200:
                            profile_data = await resp.json()
                            uid = profile_data.get("data", {}).get("id")
                            if uid:
                                users_to_sync = [uid]

                _LOGGER.info(f"Starting sync for User IDs: {users_to_sync}")

                for user_id in users_to_sync:
                    # 1. Get List
                    async with session.get(f"{base_url}/api/users/{user_id}/shopping-list", headers=headers) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        shopping_list = data.get("data", [])

                    if not shopping_list:
                        continue

                    todo_entity_id = call.data.get("target_todo_entity", "todo.bar_assistant")
                    ingredients_to_remove = []

                    # 2. Add to HA
                    for item in shopping_list:
                        ingredient = item.get("ingredient", {})
                        ing_id = ingredient.get("id")
                        name = ingredient.get("name", "Unknown Item")

                        if not ing_id:
                            continue

                        try:
                            await hass.services.async_call(
                                "todo", "add_item",
                                {"entity_id": todo_entity_id, "item": f"{name} (User {user_id})"},
                                blocking=True,
                            )
                            ingredients_to_remove.append({"id": ing_id})
                        except Exception as e:
                            _LOGGER.error(f"Failed to add {name} to HA: {e}")

                    # 3. Batch Delete
                    if ingredients_to_remove:
                        del_url = f"{base_url}/api/users/{user_id}/shopping-list/batch-delete"
                        payload = {"ingredients": ingredients_to_remove}
                        await session.post(del_url, json=payload, headers=headers)

                # Force Sensor Update
                # Note: We can't easily trigger the Todo entity update here without the entity object,
                # but it will poll automatically shortly.
                
            except Exception as e:
                _LOGGER.error(f"General error during sync: {e}")

    hass.services.async_register(DOMAIN, "sync_shopping_list", async_handle_sync)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok