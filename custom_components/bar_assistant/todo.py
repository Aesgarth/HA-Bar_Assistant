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
    
    if not user_ids:
        profile = await api.async_get_profile()
        if profile:
            user_ids = [profile.get("data", {}).get("id")]

    if user_ids:
        async_add_entities([BarAssistantTodoList(api, user_ids)], update_before_add=True)


class BarAssistantTodoList(TodoListEntity):
    """A Todo List that aggregates items and supports completed item persistence."""

    _attr_has_entity_name = True
    _attr_name = "Shopping List"
    _attr_icon = "mdi:glass-cocktail"
    
    _attr_supported_features = (
        TodoListEntityFeature.DELETE_TODO_ITEM | TodoListEntityFeature.UPDATE_TODO_ITEM
    )

    def __init__(self, api, user_ids):
        self.api = api
        self.user_ids = user_ids
        self._attr_unique_id = "bar_assistant_aggregated_shopping_list"
        self._items = []
        # Cache to store items that are completed locally but deleted from API
        self._completed_items = {} 

    async def async_update(self) -> None:
        """Pull the latest list from ALL users and combine with local completed items."""
        active_items = []
        
        # 1. Fetch Active Items from API
        for user_id in self.user_ids:
            try:
                raw_items = await self.api.async_get_shopping_list(user_id)
                for item in raw_items:
                    ingredient = item.get("ingredient", {})
                    ing_id = ingredient.get("id")
                    name = ingredient.get("name", "Unknown Item")
                    
                    if ing_id:
                        composite_uid = f"{user_id}_{ing_id}"
                        
                        # If this item is in our "completed" cache, it means the API 
                        # says it's active again (maybe added back via app). 
                        # We trust the API and remove it from completed cache.
                        if composite_uid in self._completed_items:
                            del self._completed_items[composite_uid]

                        active_items.append(
                            TodoItem(
                                uid=composite_uid,
                                summary=name,
                                status=TodoItemStatus.NEEDS_ACTION,
                            )
                        )
            except Exception as e:
                _LOGGER.error(f"Failed to fetch shopping list for user {user_id}: {e}")

        # 2. Combine Active API Items + Locally Completed Items
        self._items = active_items + list(self._completed_items.values())

    @property
    def todo_items(self) -> list[TodoItem] | None:
        return self._items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        _LOGGER.warning("Adding arbitrary text items to Bar Assistant is not supported.")

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete items. This handles both 'Trash' (Active) and 'Clear Completed' (Cached)."""
        
        items_to_delete_from_api = defaultdict(list)
        
        for uid in uids:
            if uid in self._completed_items:
                # Case A: Clearing a completed item.
                # It's already deleted from API, just remove from memory.
                del self._completed_items[uid]
            else:
                # Case B: Deleting an active item (Trash icon).
                # We need to tell the API to remove it.
                if "_" in uid:
                    try:
                        user_id_str, ing_id_str = uid.split("_")
                        items_to_delete_from_api[int(user_id_str)].append(int(ing_id_str))
                    except ValueError:
                        continue

        # Execute API Deletes for active items
        for user_id, ing_ids in items_to_delete_from_api.items():
            await self.api.async_remove_from_list(user_id, ing_ids)

        # Update local state immediately
        self._items = [i for i in self._items if i.uid not in uids]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Handle checking/unchecking items."""
        
        # Parse UID
        try:
            user_id, ing_id = map(int, item.uid.split("_"))
        except ValueError:
            return

        if item.status == TodoItemStatus.COMPLETED:
            # 1. User Checked Item -> Mark as Bought
            
            # Save to local cache so it stays visible
            self._completed_items[item.uid] = item
            
            # Remove from API (Bar Assistant)
            await self.api.async_remove_from_list(user_id, [ing_id])
            
        elif item.status == TodoItemStatus.NEEDS_ACTION:
            # 2. User Unchecked Item -> Add back to list
            
            # Remove from completed cache
            if item.uid in self._completed_items:
                del self._completed_items[item.uid]
            
            # Add back to API
            await self.api.async_add_to_list(user_id, ing_id)
        
        # Force a UI refresh to reflect the state change
        # (We update _items manually here to avoid waiting for the next poll)
        for i, existing_item in enumerate(self._items):
            if existing_item.uid == item.uid:
                self._items[i] = item
                break
