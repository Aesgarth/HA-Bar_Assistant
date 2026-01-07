import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN, 
    CONF_API_URL, 
    CONF_API_TOKEN, 
    CONF_BAR_ID, 
    CONF_SYNC_USER_IDS, 
    DEFAULT_API_URL, 
    DEFAULT_BAR_ID
)
from .api import BarAssistantAPI

class BarAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.config_info = {}
        self.available_users = []

    async def async_step_user(self, user_input=None):
        """Step 1: Get URL and Token, validate connection."""
        errors = {}
        if user_input is not None:
            api = BarAssistantAPI(
                user_input[CONF_API_URL], 
                user_input[CONF_API_TOKEN],
                user_input.get(CONF_BAR_ID, DEFAULT_BAR_ID)
            )
            
            # Validate connection
            valid = await self.hass.async_add_executor_job(api.validate_auth)
            
            if valid:
                self.config_info = user_input
                
                # Fetch users for the next step
                self.available_users = await self.hass.async_add_executor_job(api.get_users)
                
                # If we found users, show the selection form
                if self.available_users:
                    return await self.async_step_sync_users()
                
                # If no users found (e.g., non-admin token), just save what we have
                return self.async_create_entry(title="Bar Assistant", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(CONF_BAR_ID, default=DEFAULT_BAR_ID): int,
            }),
            errors=errors,
        )

    async def async_step_sync_users(self, user_input=None):
        """Step 2: Select which users to sync."""
        if user_input is not None:
            data = {**self.config_info, **user_input}
            return self.async_create_entry(title="Bar Assistant", data=data)

        user_options = {
            user["id"]: f"{user.get('name', 'Unknown')} (ID: {user['id']})"
            for user in self.available_users
        }

        return self.async_show_form(
            step_id="sync_users",
            data_schema=vol.Schema({
                vol.Optional(CONF_SYNC_USER_IDS): cv.multi_select(user_options)
            }),
        )