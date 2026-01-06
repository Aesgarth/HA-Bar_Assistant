import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID, CONF_SYNC_ALL_USERS
from .api import BarAssistantAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bar Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Retrieve settings
    api_url = entry.data[CONF_API_URL]
    api_token = entry.data[CONF_API_TOKEN]
    bar_id = entry.data.get(CONF_BAR_ID, 1)
    sync_all = entry.data.get(CONF_SYNC_ALL_USERS, False)

    # Initialize API
    api = BarAssistantAPI(api_url, api_token, bar_id)
    hass.data[DOMAIN][entry.entry_id] = api

# --- REGISTER SERVICES ---
    async def handle_sync_shopping_list(call: ServiceCall):
        """Syncs items: Bar Assistant -> HA -> Delete from Bar Assistant."""
        # 1. SCREAM TEST: If this doesn't show, the service isn't linked to this code.
        _LOGGER.error("!!! BAR ASSISTANT SYNC SERVICE STARTED !!!")

        target_list = call.data.get("target_todo_entity")
        if not target_list:
            _LOGGER.error("Sync failed: No target_todo_entity provided.")
            return

        # Determine which users to sync
        users_to_sync = []
        if sync_all:
            try:
                all_users = await hass.async_add_executor_job(api.get_users)
                users_to_sync = [u['id'] for u in all_users]
                _LOGGER.error(f"Syncing All Users: {users_to_sync}")
            except Exception as e:
                _LOGGER.error(f"Failed to fetch users: {e}")
        else:
            me = await hass.async_add_executor_job(api._ensure_user_id)
            if me: 
                users_to_sync = [me]
                _LOGGER.error(f"Syncing Single User ID: {me}")
            else:
                _LOGGER.error("Could not identify current user ID. Sync aborted.")
                return

        total_moved = 0

        for uid in users_to_sync:
            # Get list
            items = await hass.async_add_executor_job(api.get_shopping_list, uid)
            
            if not items: 
                _LOGGER.error(f"User {uid} has no items.")
                continue

            _LOGGER.error(f"User {uid} has {len(items)} items to sync.")

            for item in items:
                ingredient = item.get('ingredient', {})
                ingredient_name = ingredient.get('name', 'Unknown Item')
                
                # --- ID DEBUGGING ---
                shopping_list_id = item.get('id')
                ingredient_id = ingredient.get('id')
                
                _LOGGER.error(f"ITEM DATA: Name={ingredient_name} | ListID={shopping_list_id} | IngID={ingredient_id}")
                
                quantity = item.get('quantity', 1)
                display_name = f"{quantity}x {ingredient_name} (Bar)" if quantity > 1 else f"{ingredient_name} (Bar)"
                
                try:
                    # Add to HA
                    await hass.services.async_call(
                        "todo", "add_item",
                        {"entity_id": target_list, "item": display_name},
                        blocking=True
                    )

                    # Remove from Bar Assistant
                    if shopping_list_id:
                        _LOGGER.error(f"SENDING DELETE COMMAND FOR ID: {shopping_list_id}")
                        await hass.async_add_executor_job(api.remove_item_from_list, shopping_list_id, uid)
                        total_moved += 1
                    else:
                        _LOGGER.error(f"Cannot delete {ingredient_name} - No Shopping List ID found!")
                        
                except Exception as e:
                    _LOGGER.error(f"Failed to sync item {ingredient_name}: {e}")

        _LOGGER.error(f"Sync complete. Moved {total_moved} items total.")

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)