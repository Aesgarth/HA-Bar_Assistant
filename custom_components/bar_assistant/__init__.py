import logging
import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bar_assistant"

CONF_URL = "url"
CONF_TOKEN = "token"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL): cv.string,
                vol.Required(CONF_TOKEN): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Bar Assistant component."""
    hass.data.setdefault(DOMAIN, {})
    
    bar_config = config[DOMAIN]
    base_url = bar_config[CONF_URL].rstrip("/")
    token = bar_config[CONF_TOKEN]

    async def async_handle_sync(call: ServiceCall):
        """Handle the sync service call."""
        _LOGGER.error("!!! BAR ASSISTANT SYNC SERVICE STARTED !!!")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            try:
                # 1. Get the User ID (Profile)
                async with session.get(f"{base_url}/api/profile", headers=headers) as resp:
                    if resp.status != 200:
                        _LOGGER.error(f"Failed to get profile. Status: {resp.status}")
                        return
                    profile_data = await resp.json()
                    user_id = profile_data.get("data", {}).get("id")
                
                if not user_id:
                    _LOGGER.error("Could not determine User ID.")
                    return

                _LOGGER.error(f"Syncing Single User ID: {user_id}")

                # 2. Get the Shopping List
                async with session.get(f"{base_url}/api/shopping-list", headers=headers) as resp:
                    if resp.status != 200:
                        _LOGGER.error(f"Failed to get shopping list. Status: {resp.status}")
                        return
                    data = await resp.json()
                    shopping_list = data.get("data", [])

                _LOGGER.error(f"User {user_id} has {len(shopping_list)} items to sync.")

                todo_entity_id = "todo.bar_assistant"
                moved_count = 0

                for item in shopping_list:
                    # --- DEBUG: PRINT RAW DATA ---
                    # This will show us the full structure so we can find the correct ID key
                    _LOGGER.error(f"RAW ITEM DUMP: {item}")
                    # -----------------------------

                    ingredient = item.get("ingredient", {})
                    ing_id = ingredient.get("id")
                    name = ingredient.get("name", "Unknown Item")
                    
                    # Currently this is returning None, which is why we need the dump
                    list_id = item.get("id") 

                    _LOGGER.error(f"ITEM DATA: Name={name} | ListID={list_id} | IngID={ing_id}")

                    if not list_id:
                        _LOGGER.error(f"Cannot delete {name} - No Shopping List ID found!")
                        continue
                    
                    if not ing_id:
                        _LOGGER.error(f"Skipping {name} - No Ingredient ID found.")
                        continue

                    # 3. Add to Home Assistant Todo List
                    try:
                        await hass.services.async_call(
                            "todo",
                            "add_item",
                            {"entity_id": todo_entity_id, "item": name},
                            blocking=True,
                        )
                    except Exception as e:
                        _LOGGER.error(f"Failed to add {name} to HA todo: {e}")
                        continue

                    # 4. Remove from Bar Assistant
                    # We use the list_id to delete the specific row in the shopping list
                    delete_url = f"{base_url}/api/shopping-list/{list_id}"
                    
                    async with session.delete(delete_url, headers=headers) as del_resp:
                        if del_resp.status == 204:
                            _LOGGER.info(f"Successfully deleted {name} from Bar Assistant.")
                            moved_count += 1
                        else:
                            _LOGGER.error(f"Failed to delete {name}. Status: {del_resp.status}")

                _LOGGER.error(f"Sync complete. Moved {moved_count} items total.")

            except Exception as e:
                _LOGGER.error(f"General error during sync: {e}")

    hass.services.async_register(DOMAIN, "sync", async_handle_sync)
    return True