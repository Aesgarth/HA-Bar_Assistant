import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN
from .api import BarAssistantAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR] # We will add sensors later

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bar Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api = BarAssistantAPI(entry.data[CONF_API_URL], entry.data[CONF_API_TOKEN])
    hass.data[DOMAIN][entry.entry_id] = api


    # --- REGISTER SERVICES ---
    async def handle_sync_shopping_list(call: ServiceCall):
        """Service to pull from Bar Assistant and add to HA Todo."""
        target_list = call.data.get("target_todo_entity")
        
        if not target_list:
            _LOGGER.error("No target_todo_entity provided.")
            return

        items = await hass.async_add_executor_job(api.get_shopping_list)
        
        if not items:
            _LOGGER.info("Bar Assistant shopping list is empty.")
            return

        for item in items:
            # Docs say item contains "ingredient" object
            ingredient = item.get('ingredient', {})
            ingredient_name = ingredient.get('name', 'Unknown Item')
            
            # The shopping list entry ID (needed to delete it later)
            item_id = item.get('id') 
            
            quantity = item.get('quantity', 1)
            display_name = f"{quantity}x {ingredient_name} (Bar)" if quantity > 1 else f"{ingredient_name} (Bar)"
            
            # Add to Home Assistant Todo
            await hass.services.async_call(
                "todo",
                "add_item",
                {"entity_id": target_list, "item": display_name},
                blocking=True
            )

            # Remove from Bar Assistant
            if item_id:
                await hass.async_add_executor_job(api.remove_item_from_list, item_id)
                _LOGGER.info(f"Moved {ingredient_name} to HA.")

    hass.services.async_register(DOMAIN, "sync_shopping_list", handle_sync_shopping_list)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
