# Unreal-Engine-Plugin-Builder

**[Русский](README-RU.md)** | English

A simple GUI tool for rebuilding UE plugins on Windows using RunUAT

![UE Plugin Builder Main Interface](screenshots/main_interface.png)

## What is this?

This is a small desktop app that makes it easier to rebuild Unreal Engine plugins for different engine versions. I made it to simplify my own workflow when working across multiple UE versions.

## Features

- Rebuild plugins between different UE versions
- Auto-detects installed Unreal Engine versions (or add them manually)
- Configure build platforms, options, and parameters
- Real-time build console with syntax highlighting
- English and Russian language support
- Dark theme UI for late-night coding sessions

## Installation

### Quick Start

1. Download the release ZIP
2. Extract anywhere on your PC
3. Run `UE Plugin Builder.exe`

That's it! No installation needed.

### For Developers

If you want to run from source:

1. Make sure you have Python 3.8+ and PySide6
2. Clone this repo
3. Run `python -m ue_plugin_builder` or `python ue_plugin_builder/app.py`

## How to Use

### Basic Steps

1. **Select your plugin**: Browse to a .uplugin file or drag-drop it into the app
2. **Choose target UE version**: Select which engine version to rebuild for
3. **Set output**: Either use default location or choose custom directory
4. **Build**: Hit the "Build Plugin" button and watch the console

![Build Process](screenshots/build_process.png)

### Advanced Stuff

Click "Advanced Options" to:
- Select target platforms (Win64, Win32, Mac, Linux)
- Configure build parameters

![Advanced Options](screenshots/advanced_options.png)

## Settings

![Settings](screenshots/settings1.png)
- Add/scan Unreal Engine installations

![Settings](screenshots/settings2.png)
- Change interface language

The app saves its config in:  
`%LOCALAPPDATA%\UEPluginBuilder\`

## Troubleshooting

### No Engines Found?
Use Settings > Engines tab to manually add your UE installation or click "Scan" to auto-detect.

### Build Errors?
Check the console output for error messages. Make sure your plugin is compatible with the target engine version.

### Other Issues?
Feel free to open an issue on GitHub.

## Project Structure

```
ue_plugin_builder/
├── core/                       # Core logic (no Qt dependencies)
│   ├── config.py               # Configuration management
│   ├── engine_finder.py        # UE installation detection
│   ├── localization.py         # i18n support (EN/RU)
│   ├── platform_utils.py       # Cross-platform utilities
│   ├── plugin_builder.py       # Plugin build process
│   └── types.py                # Data types and models
├── ui/                         # UI components (PySide6)
│   ├── dialogs/                # Dialog windows
│   │   ├── advanced_options.py # Build options dialog
│   │   ├── command_dialog.py   # Command preview dialog
│   │   ├── engine_entry.py     # Engine management dialog
│   │   ├── message_dialog.py   # Custom styled dialogs
│   │   └── settings_dialog.py  # Settings dialog
│   ├── widgets/                # Reusable widgets
│   │   ├── console_widget.py   # Build console with syntax highlighting
│   │   ├── drop_overlay.py     # Drag-and-drop overlay
│   │   ├── info_card.py        # Plugin info display
│   │   ├── path_input.py       # Path input with browse button
│   │   ├── scrolling_label.py  # Animated text overflow
│   │   └── status_badge.py     # Status indicator
│   ├── icons.py                # SVG icon system
│   ├── main_window.py          # Main application window
│   └── styles.py               # UI styling and colors
├── app.py                      # Application entry point
└── ue_plugin_builder.spec      # PyInstaller build spec
```

## Adding More Languages

1. Edit `core/localization.py` to add new language entries
2. Or load a custom JSON locale file via Settings > Language

## License

MIT License

## Note

*This tool isn't affiliated with Epic Games.*
