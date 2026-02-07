# 🎨 Obsidian Plugin Demo Guide

This guide explains how to verify the **Obsidian PKM Agent** plugin, which has been successfully built and installed into a demo vault.

## ✅ Build Status

- **Plugin Source:** `B0LK13v2/obsidian-pkm-agent`
- **Build Output:** `main.js`, `manifest.json`, `styles.css`
- **Installation Path:** `B0LK13v2/demo_vault/.obsidian/plugins/obsidian-pkm-agent`
- **Status:** **Installed & Enabled**

## 🚀 How to Demo

Since this is a CLI environment, you will need to open Obsidian on your machine to see the UI.

1.  **Launch Obsidian**.
2.  **Open Folder as Vault**:
    - Click **"Open another vault"** (vault icon).
    - Select **"Open folder as vault"**.
    - Navigate to and select:
      `C:\Users\Admin\Documents\B0LK13v2\B0LK13v2\demo_vault`
3.  **Verify Plugin**:
    - Once opened, go to **Settings** -> **Community Plugins**.
    - You should see **Obsidian PKM Agent** listed and **enabled** (toggle switch on).
4.  **Test Usage**:
    - Open the Command Palette (`Ctrl+P`).
    - Type `PKM Agent` to see available commands.
    - Look for the "PKM Agent" ribbon icon (if implemented) or status bar item.

## 🛠️ Troubleshooting

If the plugin doesn't load:
1.  **Reload Obsidian**: Press `Ctrl+R` to force a reload.
2.  **Check Console**: Open Developer Tools (`Ctrl+Shift+I`) and check the **Console** tab for any errors related to `obsidian-pkm-agent`.
3.  **Rebuild**:
    If you make changes to the source code, run this command in the project root to rebuild and update the demo vault:
    ```powershell
    cd C:\Users\Admin\Documents\B0LK13v2\B0LK13v2\obsidian-pkm-agent
    npm run build
    cp main.js ../demo_vault/.obsidian/plugins/obsidian-pkm-agent/
    cp manifest.json ../demo_vault/.obsidian/plugins/obsidian-pkm-agent/
    cp styles.css ../demo_vault/.obsidian/plugins/obsidian-pkm-agent/
    ```
