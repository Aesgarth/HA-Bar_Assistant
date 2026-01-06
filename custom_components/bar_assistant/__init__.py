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
        target_list = call.data.get("target_todo_entity")
        if not target_list:
            _LOGGER.error("Sync failed: No target_todo_entity provided.")
            return

        # Determine which users to sync
        users_to_sync = []
        if sync_all:
            # Get all users from API (Requires Admin Token)
            try:
                all_users = await hass.async_add_executor_job(api.get_users)
                users_to_sync = [u['id'] for u in all_users]
                _LOGGER.info(f"Syncing shopping lists for {len(users_to_sync)} users.")
            except Exception as e:
                _LOGGER.error(f"Failed to fetch users for sync: {e}")
        else:
            # Just me
            me = await hass.async_add_executor_job(api._ensure_user_id)
            if me: 
                users_to_sync = [me]
            else:
                _LOGGER.error("Could not identify current user ID. Sync aborted.")
                return

        total_moved = 0

        # Loop through every user
        for uid in users_to_sync:
            # Get this specific user's list
            items = await hass.async_add_executor_job(api.get_shopping_list, uid)
            
            if not items: 
                continue

            for item in items:
                # Parse Item Data
                ingredient = item.get('ingredient', {})
                ingredient_name = ingredient.get('name', 'Unknown Item')
                
                # --- DEBUGGING IDs ---
                shopping_list_id = item.get('id')         # ID of the row in the shopping list
                ingredient_id = ingredient.get('id')      # ID of the actual vodka/lime
                
                _LOGGER.warning(f"PROCESSING {ingredient_name}: Shopping List ID: {shopping_list_id} | Ingredient ID: {ingredient_id}")
                # ---------------------

                quantity = item.get('quantity', 1)
                
                # Format Name for HA
                # If syncing multiple users, you might want to tag who asked for it, 
                # but for now we keep it simple.
                display_name = f"{quantity}x {ingredient_name} (Bar)" if quantity > 1 else f"{ingredient_name} (Bar)"
                
                try:
                    # 1. Add to Home Assistant
                    await hass.services.async_call(
                        "todo", "add_item",
                        {"entity_id": target_list, "item": display_name},
                        blocking=True
                    )

                    # 2. Remove from Bar Assistant (Only if HA add succeeded)
                    if shopping_list_id:
                        _LOGGER.info(f"Attempting to delete Shopping List ID: {shopping_list_id} for User {uid}")
                        await hass.async_add_executor_job(api.remove_item_from_list, shopping_list_id, uid)
                        total_moved += 1
                    else:
                        _LOGGER.error(f"Cannot delete {ingredient_name} - No Shopping List ID found! (Data: {item})")
                        
                except Exception as e:
                    _LOGGER.error(f"Failed to sync item {ingredient_name}: {e}")

        _LOGGER.info(f"Sync complete. Moved {total_moved} items total.")

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)