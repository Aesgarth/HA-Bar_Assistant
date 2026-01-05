import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID
from .api import BarAssistantAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bar Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Retrieve settings, defaulting to 1 if missing (backward compatibility)
    api_url = entry.data[CONF_API_URL]
    api_token = entry.data[CONF_API_TOKEN]
    bar_id = entry.data.get(CONF_BAR_ID, 1)

    # Initialize API with the explicit Bar ID
    api = BarAssistantAPI(api_url, api_token, bar_id)
    hass.data[DOMAIN][entry.entry_id] = api

    # --- REGISTER SERVICES ---
    async def handle_sync_shopping_list(call: ServiceCall):
        target_list = call.data.get("target_todo_entity")
        if not target_list: return

        items = await hass.async_add_executor_job(api.get_shopping_list)
        
        if not items:
            _LOGGER.info("Bar Assistant shopping list is empty.")
            return

        for item in items:
            ingredient = item.get('ingredient', {})
            ingredient_name = ingredient.get('name', 'Unknown Item')
            item_id = item.get('id')
            
            # Display name logic
            quantity = item.get('quantity', 1)
            display_name = f"{quantity}x {ingredient_name} (Bar)" if quantity > 1 else f"{ingredient_name} (Bar)"
            
            await hass.services.async_call(
                "todo", "add_item",
                {"entity_id": target_list, "item": display_name},
                blocking=True
            )

            if item_id:
                await hass.async_add_executor_job(api.remove_item_from_list, item_id)
                _LOGGER.info(f"Moved {ingredient_name} to HA.")

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
