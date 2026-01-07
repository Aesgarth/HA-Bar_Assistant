import logging
from collections import defaultdict
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
    """Set up the Bar Assistant Todo List."""
    api = hass.data[DOMAIN][entry.entry_id]
    user_ids = entry.data.get("sync_user_ids", [])
    
    # Fallback: If no users selected, fetch the authenticated user's profile
    if not user_ids:
        profile = await api.async_get_profile()
        if profile:
            user_ids = [profile.get("data", {}).get("id")]

    # Create ONE aggregated list for all users
    if user_ids:
        async_add_entities([BarAssistantTodoList(api, user_ids)], update_before_add=True)


class BarAssistantTodoList(TodoListEntity):
    """A single Todo List that aggregates items from all selected Bar Assistant users."""

    _attr_has_entity_name = True
    _attr_name = "Shopping List"  # Resulting ID: todo.bar_assistant_shopping_list
    _attr_icon = "mdi:glass-cocktail"
    
    _attr_supported_features = (
        TodoListEntityFeature.DELETE_TODO_ITEM | TodoListEntityFeature.UPDATE_TODO_ITEM
    )

    def __init__(self, api, user_ids):
        self.api = api
        self.user_ids = user_ids
        # Stable unique ID so the entity persistence works
        self._attr_unique_id = "bar_assistant_aggregated_shopping_list"
        self._items = []

    async def async_update(self) -> None:
        """Pull the latest list from ALL users and combine them."""
        combined_items = []
        
        for user_id in self.user_ids:
            try:
                raw_items = await self.api.async_get_shopping_list(user_id)
                for item in raw_items:
                    ingredient = item.get("ingredient", {})
                    ing_id = ingredient.get("id")
                    name = ingredient.get("name", "Unknown Item")
                    
                    if ing_id:
                        # Composite UID: user_id + "_" + ingredient_id
                        # This lets us know WHO to delete the item from later
                        composite_uid = f"{user_id}_{ing_id}"
                        
                        combined_items.append(
                            TodoItem(
                                uid=composite_uid,
                                summary=name,
                                status=TodoItemStatus.NEEDS_ACTION,
                            )
                        )
            except Exception as e:
                _LOGGER.error(f"Failed to fetch shopping list for user {user_id}: {e}")

        self._items = combined_items

    @property
    def todo_items(self) -> list[TodoItem] | None:
        return self._items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item. (Not supported yet)."""
        _LOGGER.warning("Adding arbitrary text items to Bar Assistant is not supported.")

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete items from the list, handling multiple users."""
        
        # Group items by User ID so we can batch delete efficiently
        items_by_user = defaultdict(list)
        
        for uid in uids:
            if "_" in uid:
                try:
                    user_id_str, ing_id_str = uid.split("_")
                    items_by_user[int(user_id_str)].append(int(ing_id_str))
                except ValueError:
                    _LOGGER.error(f"Invalid item UID format: {uid}")
                    continue

        # Execute Batch Deletes per User
        for user_id, ing_ids in items_by_user.items():
            _LOGGER.debug(f"Removing items {ing_ids} for User {user_id}")
            await self.api.async_remove_from_list(user_id, ing_ids)

        # Optimistically update the local list to remove checked items immediately
        self._items = [i for i in self._items if i.uid not in uids]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item. If marked completed, delete it."""
        if item.status == TodoItemStatus.COMPLETED:
            await self.async_delete_todo_items([item.uid])
