from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BarAssistantCocktailCount(api),
        BarAssistantTotalCocktails(api),  # <--- New
        BarAssistantShoppingCount(api)
    ], True)

class BarAssistantCocktailCount(SensorEntity):
    """Cocktails you can make (Shelf)."""
    def __init__(self, api):
        self._api = api
        self._attr_name = "Cocktails I Can Make"
        self._attr_unique_id = "bar_assistant_can_make_count"
        self._attr_native_unit_of_measurement = "drinks"
        self._attr_icon = "mdi:glass-cocktail"
        self._state = 0
        self._extra_attributes = {}

    def update(self):
        cocktails = self._api.get_cocktails()
        self._state = len(cocktails)
        drink_names = sorted([c['name'] for c in cocktails])
        self._extra_attributes = {"cocktail_list": drink_names}
    
    @property
    def native_value(self): return self._state
    @property
    def extra_state_attributes(self): return self._extra_attributes

class BarAssistantTotalCocktails(SensorEntity):
    """Total Cocktails in the database (Menu)."""
    def __init__(self, api):
        self._api = api
        self._attr_name = "Total Bar Menu"
        self._attr_unique_id = "bar_assistant_total_menu_count"
        self._attr_native_unit_of_measurement = "drinks"
        self._attr_icon = "mdi:book-open-variant"
        self._state = 0

    def update(self):
        cocktails = self._api.get_total_cocktails()
        self._state = len(cocktails)

    @property
    def native_value(self): return self._state

class BarAssistantShoppingCount(SensorEntity):
    """Items on the shopping list (My User Only)."""
    def __init__(self, api):
        self._api = api
        self._attr_name = "Bar Shopping List Items"
        self._attr_unique_id = "bar_assistant_shopping_count"
        self._attr_native_unit_of_measurement = "items"
        self._attr_icon = "mdi:cart-outline"
        self._state = 0

    def update(self):
        items = self._api.get_shopping_list()
        self._state = len(items)

    @property
    def native_value(self): return self._state
