import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_BAR_ID, CONF_SYNC_ALL_USERS, DEFAULT_API_URL, DEFAULT_BAR_ID, DEFAULT_SYNC_ALL_USERS
from .api import BarAssistantAPI

class BarAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api = BarAssistantAPI(
                user_input[CONF_API_URL], 
                user_input[CONF_API_TOKEN],
                user_input.get(CONF_BAR_ID, DEFAULT_BAR_ID)
            )
            valid = await self.hass.async_add_executor_job(api.validate_auth)
            if valid:
                return self.async_create_entry(title="Bar Assistant", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(CONF_BAR_ID, default=DEFAULT_BAR_ID): int,
                vol.Optional(CONF_SYNC_ALL_USERS, default=DEFAULT_SYNC_ALL_USERS): bool, # <--- New Checkbox
            }),
            errors=errors,
        )
