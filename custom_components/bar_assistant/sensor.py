from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BarAssistantCocktailCount(api)], True)

class BarAssistantCocktailCount(SensorEntity):
    """Sensor showing how many cocktails you can make."""

    def __init__(self, api):
        self._api = api
        self._attr_name = "Cocktails I Can Make"
        self._attr_unique_id = "bar_assistant_can_make_count"
        self._attr_native_unit_of_measurement = "drinks"
        self._state = 0
        self._extra_attributes = {}

    def update(self):
        """Fetch new state data for the sensor."""
        cocktails = self._api.get_cocktails()
        self._state = len(cocktails)
        
        # Store the list of cocktail names in attributes for the dashboard
        drink_names = [c['name'] for c in cocktails]
        self._extra_attributes = {"cocktail_list": drink_names}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._extra_attributes
