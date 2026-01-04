# Bar Assistant for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Aesgarth/HA-Bar_Assistant)](https://github.com/Aesgarth/HA-Bar_Assistant/releases)

A custom integration to connect **Home Assistant** with **[Bar Assistant](https://bar-assistant.io)**.

This integration allows you to sync your Bar Assistant shopping list directly into a Home Assistant To-Do list and view how many cocktails you can currently make based on your inventory.

## Features

* **Shopping List Sync:** A dedicated service (`bar_assistant.sync_shopping_list`) that:
    1.  Pulls items from your Bar Assistant shopping list.
    2.  Adds them to a specific Home Assistant To-Do list (e.g., `todo.shopping_list`).
    3.  **Automatically removes** the items from Bar Assistant to prevent duplication.
* **Cocktail Sensor:** A sensor (`sensor.cocktails_i_can_make`) showing the count of drinks you can currently make.
    * *Attributes:* Contains a list of the actual cocktail names, perfect for displaying on a dashboard.

---

## Installation

### Option 1: HACS (Recommended)

Since this is a custom integration, you must add it as a custom repository in HACS first.

1.  Open **HACS** in Home Assistant.
2.  Click the **3 dots** in the top right corner and select **Custom repositories**.
3.  Paste the URL: `https://github.com/Aesgarth/HA-Bar_Assistant`
4.  Select **Integration** as the category.
5.  Click **Add**.
6.  Now search for "Bar Assistant" in HACS and click **Download**.
7.  **Restart Home Assistant**.

### Option 2: Manual Installation

1.  Download the latest release from this repository.
2.  Copy the `custom_components/bar_assistant` folder into your Home Assistant's `custom_components` directory.
3.  **Restart Home Assistant**.

---

## Configuration

1.  **Get your Credentials:**
    * **URL:** The URL to your Bar Assistant instance (e.g., `https://my-bar.com/bar` or `http://192.168.1.50:8000`).
    * **API Token:** Log in to your Bar Assistant, go to **Settings / Profile**, and generate a Personal Access Token (or copy your existing Bearer token).

2.  **Add Integration:**
    * In Home Assistant, go to **Settings > Devices & Services**.
    * Click **+ Add Integration**.
    * Search for **Bar Assistant**.
    * Enter your **API URL** and **API Token**.

---

## Usage

### 1. Syncing the Shopping List

To sync your items, you must call the service. You can do this via a Button on your dashboard or an Automation.

**Service Name:** `bar_assistant.sync_shopping_list`

#### Example Automation (YAML)
This automation runs every morning at 8 AM, or you can trigger it manually.

```yaml
alias: "Sync Bar Shopping List"
description: "Moves items from Bar Assistant to HA Shopping List"
trigger:
  - platform: time
    at: "08:00:00"
action:
  - service: bar_assistant.sync_shopping_list
    data:
      target_todo_entity: todo.shopping_list
```

### 2. Dashboard Card (Cocktails)
You can use the sensor attributes to list available drinks on your dashboard using a Markdown card.

Markdown Card Code:

YAML
```
type: markdown
content: >
  ## 🍸 Cocktail Menu
  
  You can currently make **{{ states('sensor.cocktails_i_can_make') }}** drinks!
  
  ---
  
  {% for drink in state_attr('sensor.cocktails_i_can_make', 'cocktail_list') -%}
  - {{ drink }}
  {% endfor %}
```
