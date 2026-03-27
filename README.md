# ⚠️ This repository is archived

**This project has been superseded by [UE Forge](https://github.com/PsinaDev/ue-forge)** — a modular desktop toolkit for Unreal Engine automation.

UE Forge includes the Plugin Builder along with additional tools: Renamer, Include Optimizer, and Commandlet Runner — all in a single host window with a sidebar interface.

### Migration

```bash
git clone --recurse-submodules https://github.com/PsinaDev/ue-forge.git
cd ue-forge
pip install -r requirements.txt
python -m ue_forge
```

The Plugin Builder is available as `python -m ue_forge.plugin_builder` for standalone use.

---

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
3. Run `python -m source` or `python source/app.py`

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

## License

MIT License

## Note

*This tool isn't affiliated with Epic Games.*
