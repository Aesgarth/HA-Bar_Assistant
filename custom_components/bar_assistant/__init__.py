import logging
import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID, DEFAULT_BAR_ID
from .api import BarAssistantAPI  # <--- Import the API class for sensors

_LOGGER = logging.getLogger(__name__)

# List of platforms to support (sensors, etc.)
PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Default setup for the component. Required for HA."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bar Assistant from a config entry (UI Config)."""
    
    # 1. Retrieve Config Data
    config_data = entry.data
    base_url = config_data.get(CONF_API_URL, "").rstrip("/")
    token = config_data.get(CONF_API_TOKEN, "")
    bar_id = config_data.get(CONF_BAR_ID, DEFAULT_BAR_ID)

    # Legacy config fallback
    if not base_url:
        base_url = config_data.get("url", "").rstrip("/")
    if not token:
        token = config_data.get("token", "")

    # 2. Store API instance for Sensors to use
    # This fixes the "no longer provided" error by making the API available to sensor.py
    hass.data.setdefault(DOMAIN, {})
    api_client = BarAssistantAPI(base_url, token, bar_id)
    hass.data[DOMAIN][entry.entry_id] = api_client

    # 3. Load the Sensor Platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 4. Define the Sync Service (The "Batch Delete" version)
    async def async_handle_sync(call: ServiceCall):
        """Handle the sync service call."""
        _LOGGER.info("!!! BAR ASSISTANT SYNC SERVICE STARTED !!!")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Bar-Assistant-Bar-Id": str(bar_id),
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Get User ID
                async with session.get(f"{base_url}/api/profile", headers=headers) as resp:
                    if resp.status != 200:
                        _LOGGER.error(f"Failed to get profile. Status: {resp.status}")
                        return
                    profile_data = await resp.json()
                    user_id = profile_data.get("data", {}).get("id")
                
                if not user_id:
                    _LOGGER.error("Could not determine User ID.")
                    return

                # Get Shopping List
                async with session.get(f"{base_url}/api/users/{user_id}/shopping-list", headers=headers) as resp:
                    if resp.status != 200:
                        _LOGGER.error(f"Failed to get shopping list. Status: {resp.status}")
                        return
                    data = await resp.json()
                    shopping_list = data.get("data", [])

                _LOGGER.info(f"User {user_id} has {len(shopping_list)} items to sync.")

                todo_entity_id = call.data.get("target_todo_entity", "todo.bar_assistant")
                ingredients_to_remove = []

                # Process Items
                for item in shopping_list:
                    ingredient = item.get("ingredient", {})
                    ing_id = ingredient.get("id")
                    name = ingredient.get("name", "Unknown Item")

                    if not ing_id:
                        _LOGGER.warning(f"Skipping {name} - No Ingredient ID found.")
                        continue

                    # Add to HA Todo
                    try:
                        await hass.services.async_call(
                            "todo",
                            "add_item",
                            {"entity_id": todo_entity_id, "item": name},
                            blocking=True,
                        )
                        # Only mark for deletion if successfully added to HA
                        ingredients_to_remove.append({"id": ing_id})
                        
                    except Exception as e:
                        _LOGGER.error(f"Failed to add {name} to HA todo: {e}")
                        continue

                # Batch Delete from Bar Assistant
                if ingredients_to_remove:
                    delete_url = f"{base_url}/api/users/{user_id}/shopping-list/batch-delete"
                    payload = {"ingredients": ingredients_to_remove}
                    
                    _LOGGER.debug(f"Batch deleting items: {payload}")

                    async with session.post(delete_url, json=payload, headers=headers) as del_resp:
                        if del_resp.status in [200, 204]:
                            _LOGGER.info(f"Successfully removed {len(ingredients_to_remove)} items from Bar Assistant.")
                            
                            # Update the sensors immediately after sync so the counts are correct
                            # This forces the sensor entities to refresh their state
                            for entity in hass.data[DOMAIN].get("entities", []):
                                entity.async_schedule_update_ha_state(True)
                        else:
                            text = await del_resp.text()
                            _LOGGER.error(f"Failed to batch delete items. Status: {del_resp.status} | Response: {text}")
                else:
                    _LOGGER.info("No items to delete.")

            except Exception as e:
                _LOGGER.error(f"General error during sync: {e}")

    # Register the service
    hass.services.async_register(DOMAIN, "sync_shopping_list", async_handle_sync)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok