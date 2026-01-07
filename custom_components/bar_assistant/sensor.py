from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    
    # Determine which user to track for "My Shopping List"
    # Defaults to the first selected user or the profile user
    user_id = None
    selected_ids = entry.data.get("sync_user_ids", [])
    if selected_ids:
        user_id = selected_ids[0]
    else:
        # Fetch profile if no specific user selected
        profile = await api.async_get_profile()
        if profile:
            user_id = profile.get("data", {}).get("id")

    entities = [
        BarAssistantTotalCocktails(api),
    ]

    if user_id:
        entities.append(BarAssistantCocktailCount(api, user_id))
        entities.append(BarAssistantShoppingCount(api, user_id))

    async_add_entities(entities, True)

class BarAssistantCocktailCount(SensorEntity):
    """Cocktails you can make (Shelf)."""
    def __init__(self, api, user_id):
        self._api = api
        self._user_id = user_id
        self._attr_name = "Cocktails I Can Make"
        self._attr_unique_id = f"bar_assistant_can_make_{user_id}"
        self._attr_native_unit_of_measurement = "drinks"
        self._attr_icon = "mdi:glass-cocktail"
        self._state = 0
        self._extra_attributes = {}

    async def async_update(self):
        cocktails = await self._api.async_get_cocktails(self._user_id)
        self._state = len(cocktails)
        drink_names = sorted([c.get('name', 'Unknown') for c in cocktails])
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

    async def async_update(self):
        cocktails = await self._api.async_get_total_cocktails()
        self._state = len(cocktails)

    @property
    def native_value(self): return self._state

class BarAssistantShoppingCount(SensorEntity):
    """Items on the shopping list."""
    def __init__(self, api, user_id):
        self._api = api
        self._user_id = user_id
        self._attr_name = "Bar Shopping List Items"
        self._attr_unique_id = f"bar_assistant_shopping_count_{user_id}"
        self._attr_native_unit_of_measurement = "items"
        self._attr_icon = "mdi:cart-outline"
        self._state = 0

    async def async_update(self):
        items = await self._api.async_get_shopping_list(self._user_id)
        self._state = len(items)

    @property
    def native_value(self): return self._state