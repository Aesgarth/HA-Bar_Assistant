import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID, CONF_SYNC_ALL_USERS
from .api import BarAssistantAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    api_url = entry.data[CONF_API_URL]
    api_token = entry.data[CONF_API_TOKEN]
    bar_id = entry.data.get(CONF_BAR_ID, 1)
    sync_all = entry.data.get(CONF_SYNC_ALL_USERS, False)

    api = BarAssistantAPI(api_url, api_token, bar_id)
    hass.data[DOMAIN][entry.entry_id] = api

    async def handle_sync_shopping_list(call: ServiceCall):
        target_list = call.data.get("target_todo_entity")
        if not target_list: return

        # Determine which users to sync
        users_to_sync = []
        if sync_all:
            # Get all users from API
            all_users = await hass.async_add_executor_job(api.get_users)
            users_to_sync = [u['id'] for u in all_users]
            _LOGGER.info(f"Syncing shopping lists for {len(users_to_sync)} users.")
        else:
            # Just me
            me = await hass.async_add_executor_job(api._ensure_user_id)
            if me: users_to_sync = [me]

        total_moved = 0

        # Loop through every user
        for uid in users_to_sync:
            # Get this specific user's list
            items = await hass.async_add_executor_job(api.get_shopping_list, uid)
            
            if not items: continue

            for item in items:
                ingredient_name = item.get('ingredient', {}).get('name', 'Unknown')
                item_id = item.get('id')
                quantity = item.get('quantity', 1)
                
                # Tagging the user is helpful if syncing multiple people
                # optional: suffix = f" (User {uid})" if sync_all else ""
                
                display_name = f"{quantity}x {ingredient_name} (Bar)" if quantity > 1 else f"{ingredient_name} (Bar)"
                
                try:
                    # Add to HA
                    await hass.services.async_call(
                        "todo", "add_item",
                        {"entity_id": target_list, "item": display_name},
                        blocking=True
                    )

                    # Remove from THIS user's list
                    if item_id:
                        await hass.async_add_executor_job(api.remove_item_from_list, item_id, uid)
                        total_moved += 1
                except Exception as e:
                    _LOGGER.error(f"Failed to sync item {ingredient_name}: {e}")

        _LOGGER.info(f"Sync complete. Moved {total_moved} items total.")

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
