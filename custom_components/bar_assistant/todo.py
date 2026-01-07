import logging
from homeassistant.components.todo import (
    TodoListEntity,
    TodoListEntityFeature,
    TodoItem,
    TodoItemStatus,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    user_ids = entry.data.get("sync_user_ids", [])
    
    if not user_ids:
        profile = await api.async_get_profile()
        if profile:
            user_ids = [profile.get("data", {}).get("id")]

    entities = []
    for user_id in user_ids:
        entities.append(BarAssistantTodoList(api, user_id))

    async_add_entities(entities, update_before_add=True)

class BarAssistantTodoList(TodoListEntity):
    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.DELETE_TODO_ITEM | TodoItemStatus.COMPLETED
    )

    def __init__(self, api, user_id):
        self.api = api
        self.user_id = user_id
        self._attr_unique_id = f"bar_assistant_shopping_list_{user_id}"
        self._attr_name = f"Shopping List (User {user_id})"
        self._items = []

    async def async_update(self) -> None:
        raw_items = await self.api.async_get_shopping_list(self.user_id)
        self._items = []
        for item in raw_items:
            ingredient = item.get("ingredient", {})
            ing_id = ingredient.get("id")
            name = ingredient.get("name", "Unknown Item")
            
            if ing_id:
                self._items.append(
                    TodoItem(
                        uid=str(ing_id),
                        summary=name,
                        status=TodoItemStatus.NEEDS_ACTION,
                    )
                )

    @property
    def todo_items(self) -> list[TodoItem] | None:
        return self._items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        _LOGGER.warning("Adding arbitrary text items to Bar Assistant is not supported.")

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        ids_to_delete = [int(uid) for uid in uids if uid.isdigit()]
        if await self.api.async_remove_from_list(self.user_id, ids_to_delete):
            self._items = [i for i in self._items if i.uid not in uids]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        if item.status == TodoItemStatus.COMPLETED:
            await self.async_delete_todo_items([item.uid])