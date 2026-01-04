import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, DEFAULT_API_URL
from .api import BarAssistantAPI

class BarAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bar Assistant."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Validate the connection
            api = BarAssistantAPI(user_input[CONF_API_URL], user_input[CONF_API_TOKEN])
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
            }),
            errors=errors,
        )
