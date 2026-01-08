# Bar Assistant for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Aesgarth/HA-Bar_Assistant)](https://github.com/Aesgarth/HA-Bar_Assistant/releases)

A custom integration to connect **Home Assistant** with **[Bar Assistant](https://bar-assistant.io)**.

This integration brings your Bar Assistant shopping list directly into Home Assistant as a **native To-Do list** and provides sensors to track your inventory and menu capabilities.

## Features

* **Interactive Shopping List (`todo.bar_assistant_shopping_list`):**
    * **2-Way Sync:** Checking an item in Home Assistant immediately removes it from Bar Assistant (marking it as bought).
    * **Aggregated View:** Combines shopping list items from multiple Bar Assistant users into a single, unified list.
    * **Persistence:** "Checked" items stay visible in Home Assistant until you clear them, just like a standard shopping list.
* **Smart Sensors:**
    * `sensor.cocktails_i_can_make`: Counts how many recipes you can currently make with your shelf.
    * `sensor.total_bar_menu`: Counts the total number of recipes in your database.
    * `sensor.bar_shopping_list_items`: Counts the number of active items on the shopping list.
* **Sync Service:** A service (`bar_assistant.sync_shopping_list`) is still available for advanced users who want to move items to a different list via automation.

---

## Installation

### Option 1: HACS (Recommended)

1.  Open **HACS** in Home Assistant.
2.  Click the **3 dots** in the top right corner and select **Custom repositories**.
3.  Paste the URL: `https://github.com/Aesgarth/HA-Bar_Assistant`
4.  Select **Integration** as the category.
5.  Click **Add**.
6.  Search for "Bar Assistant" and click **Download**.
7.  **Restart Home Assistant**.

### Option 2: Manual Installation

1.  Download the latest release from this repository.
2.  Copy the `custom_components/bar_assistant` folder into your Home Assistant's `custom_components` directory.
3.  **Restart Home Assistant**.

---

## Configuration

1.  **Get your Credentials:**
    * **URL:** The URL to your Bar Assistant instance (e.g., `https://my-bar.com/bar` or `http://192.168.1.50:8000`).
    * **API Token:** Log in to your Bar Assistant, go to **Settings / Profile**, and generate a Personal Access Token.

2.  **Add Integration:**
    * Go to **Settings > Devices & Services** in Home Assistant.
    * Click **+ Add Integration**.
    * Search for **Bar Assistant**.

3.  **Setup Steps:**
    * **Step 1:** Enter your API URL and Token.
    * **Step 2:** Select which **Users** you want to sync. The integration will aggregate shopping list items from all selected users into one list.

---

## Usage

### 1. The Shopping List

Once installed, a new entity named `todo.bar_assistant_shopping_list` will appear.
* **Add it to your Dashboard:** Use the standard **To-do List** card.
* **How it works:**
    * **View:** Shows ingredients added to the shopping list in Bar Assistant.
    * **Complete:** Click the checkbox to mark an item as bought. It will be removed from Bar Assistant immediately.
    * **Clear:** Use the "Clear Completed" button in Home Assistant to remove checked items from your view.

### 2. Dashboard Card (Cocktail Menu)

You can use the sensor attributes to list available drinks on your dashboard.

**Markdown Card Example:**

```yaml
type: markdown
content: >
  ## 🍸 Bar Menu
  
  **Shelf:** {{ states('sensor.cocktails_i_can_make') }} drinks available
  **Total Menu:** {{ states('sensor.total_bar_menu') }} recipes
  
  ---
  ### 🍹 What can I make?
  
  {% for drink in state_attr('sensor.cocktails_i_can_make', 'cocktail_list') -%}
  - {{ drink }}
  {% endfor %}
```
### 3. Automation Service (Legacy)
If you prefer to move items to a different list (like todo.groceries) instead of using the dedicated Bar Assistant list, you can use the sync service.

Service: bar_assistant.sync_shopping_list

```YAML

alias: "Move Bar Items to Main Grocery List"
trigger:
  - platform: time
    at: "08:00:00"
action:
  - service: bar_assistant.sync_shopping_list
    data:
      target_todo_entity: todo.groceries
```
Note: This service moves items and deletes them from Bar Assistant immediately.
