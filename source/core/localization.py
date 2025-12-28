"""
Localization system for UE Plugin Builder.
Supports multiple languages with auto-detection and custom JSON localization files.
"""
import json
import locale
from pathlib import Path
from typing import Dict, Optional, Any


# Default translations
_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Window
        "app_title": "UE Plugin Builder",
        "ready": "Ready",
        "building": "Building...",
        "success": "Success",
        "failed": "Failed",
        "cancelled": "Cancelled",
        
        # Plugin section
        "plugin": "Plugin",
        "select_uplugin_file": "Select .uplugin file",
        "path_to_plugin_file": "Path to plugin file...",
        "drag_drop_hint": "Or drag & drop plugin folder here",
        "invalid_drop_file": "Invalid file or folder doesn't contain .uplugin",
        "plugin_information": "Plugin Information",
        "no_information": "No information. Please select a file...",
        
        # Plugin info fields
        "name": "Name",
        "version": "Version",
        "engine_version": "Engine Version",
        "modules": "Modules",
        "category": "Category",
        "author": "Author",
        "description": "Description",
        "dependencies": "Dependencies",
        "platforms": "Platforms",
        "content": "Content",
        "beta": "Beta",
        "experimental": "Experimental",
        "yes": "Yes",
        "no": "No",
        
        # Target engine
        "target_engine": "Target Engine",
        "build_for": "Build for:",
        "select_version": "Select version...",
        "rescan_engines": "Rescan for engines",
        "version_warning": "Warning: Target version matches plugin version!",
        
        # Output directory
        "output_directory": "Output Directory",
        "to_parent_directory": "To parent directory",
        "select_another_directory": "Select another directory",
        "output_path": "Output path...",
        
        # Console
        "console_output": "Console Output",
        "copied": "Copied!",
        "copy_tooltip": "Copy to clipboard",
        
        # Combo copy easter egg
        "combo_copy_0": "Copied!",
        "combo_copy_1": "Double copy!",
        "combo_copy_2": "Triple copy!",
        "combo_copy_3": "Combo copy!",
        "combo_copy_4": "Mega copy!",
        "combo_copy_5": "Super copy!",
        "combo_copy_6": "Ultra copy!",
        "combo_copy_7": "GIGA COPY!!!",
        "combo_copy_8": "☆ LEGENDARY ☆",
        "combo_copy_9": "✦ DIVINE ✦",
        "combo_copy_10": "⚡ COSMIC ⚡",
        "combo_copy_11": "🔥 APOCALYPSE 🔥",
        "combo_post_0": "Maybe that's enough?",
        "combo_post_1": "Seriously, stop",
        "combo_post_2": "Last warning!",
        "combo_post_3": "Button will be taken away in...",
        "combo_button_gone": "Bye-bye button! 👋",
        
        # Buttons
        "advanced_options": "Advanced Options",
        "show_command": "Show Command",
        "uat_help": "UAT Help",
        "clear_console": "Clear Console",
        "build_plugin": "Build Plugin",
        "cancel": "Cancel",
        "ok": "OK",
        "browse": "Browse...",
        "add": "Add",
        "remove": "Remove",
        "close": "Close",
        
        # Settings / Engine dialog
        "settings": "Settings",
        "manage_engine_installations": "Manage Engine Installations",
        "registered_engines": "Registered Engines",
        "double_click_hint": "Double-click an engine to open its folder",
        "remove_selected": "Remove Selected",
        "scan_for_engines": "Scan for Engines",
        "add_engine_manually": "Add Engine Manually",
        "path_to_ue_installation": "Path to Unreal Engine installation...",
        "auto_detect": "Auto-detect...",
        "add_engine": "Add Engine",
        "path_not_exist": "Path does not exist",
        "not_valid_engine": "Not a valid Unreal Engine installation",
        "detected_ue": "Detected UE",
        "valid_engine_unknown_version": "Valid engine, version unknown",
        "engine_added": "Engine added successfully",
        "remove_engine_confirm": "Remove UE {version} from the list?",
        "version_exists": "UE {version} already exists. Replace it?",
        "version_required": "Please enter a version number (e.g., 5.4)",
        "scanning_engines": "Scanning for engines...",
        "found_engines": "Found {count} engine(s)",
        "found_engines_hint": "If some engines are missing, add them manually below",
        "no_engines_found": "No engines found",
        "folder_not_found": "Folder does not exist",
        "could_not_open_folder": "Could not open folder",
        
        # Advanced options
        "advanced_build_options": "Advanced Build Options",
        "target_platforms": "Target Platforms",
        "windows_64": "Windows 64-bit",
        "windows_32": "Windows 32-bit",
        "linux": "Linux",
        "macos": "macOS",
        "build_options": "Build Options",
        "no_host_platform": "Do not compile for host platform",
        "strict_includes": "Strict includes (disable PCH and unity build)",
        "unversioned": "Unversioned (no engine version in descriptor)",
        "additional_parameters": "Additional Parameters",
        "additional_params_hint": "Enter additional command line parameters.\nExample: -Param1=Value1 -Flag -Param2=\"Value with spaces\"",
        
        # Command dialog
        "build_command": "Build Command",
        "copy_command": "Copy Command",
        "command_copied": "Command copied to clipboard",
        
        # Localization settings
        "language": "Language",
        "language_settings": "Language Settings",
        "select_language": "Select language",
        "load_custom_locale": "Load custom locale (JSON)",
        "no_custom_locale": "No custom locale loaded",
        "language_restart_note": "Note: Language change requires application restart.",
        "locale_loaded": "Locale loaded successfully",
        "locale_load_error": "Failed to load locale file",
        "restart_to_apply": "Please restart the application to apply the language change.",
        "select_ue_installation": "Select Unreal Engine installation",
        
        # Validation messages
        "validation_error": "Validation Error",
        "select_plugin_file": "Please select a plugin file.",
        "plugin_not_found": "Plugin file not found.",
        "select_target_engine": "Please select a target engine.",
        "engine_not_found": "Selected engine not found.",
        "specify_output_dir": "Please specify output directory.",
        
        # Build messages
        "searching_engines": "Searching for Unreal Engine installations...",
        "found_n_engines": "Found {count} engine(s)",
        "no_engines_add_manually": "No engines found. Add one manually via Settings.",
        "plugin_selected": "Plugin selected: {path}",
        "applied_options": "Applied options: {options}",
        "build_complete": "Build Complete",
        "build_successful": "Plugin built successfully!\n\nOutput: {path}",
        "build_failed": "Build Failed",
        "build_failed_msg": "Build failed:\n\n{error}",
        "build_in_progress": "Build in Progress",
        "cancel_and_exit": "A build is in progress. Cancel and exit?",
        "error": "Error",
        "generate_command_error": "Failed to generate build command. Check all parameters.",
    },
    
    "ru": {
        # Window
        "app_title": "UE Plugin Builder",
        "ready": "Готово",
        "building": "Сборка...",
        "success": "Успех",
        "failed": "Провал",
        "cancelled": "Отменено",
        
        # Plugin section
        "plugin": "Плагин",
        "select_uplugin_file": "Выберите файл .uplugin",
        "path_to_plugin_file": "Путь к файлу плагина...",
        "drag_drop_hint": "Или перетащите папку с плагином сюда",
        "invalid_drop_file": "Неверный файл или папка не содержит .uplugin",
        "plugin_information": "Информация о плагине",
        "no_information": "Нет данных. Выберите файл...",
        
        # Plugin info fields
        "name": "Имя",
        "version": "Версия",
        "engine_version": "Версия движка",
        "modules": "Модули",
        "category": "Категория",
        "author": "Автор",
        "description": "Описание",
        "dependencies": "Зависимости",
        "platforms": "Платформы",
        "content": "Контент",
        "beta": "Бета",
        "experimental": "Эксперимент.",
        "yes": "Да",
        "no": "Нет",
        
        # Target engine
        "target_engine": "Целевой движок",
        "build_for": "Собрать для:",
        "select_version": "Выберите версию...",
        "rescan_engines": "Обновить список движков",
        "version_warning": "Внимание: целевая версия совпадает с версией плагина!",
        
        # Output directory
        "output_directory": "Папка назначения",
        "to_parent_directory": "В родительскую папку",
        "select_another_directory": "Указать другую папку",
        "output_path": "Путь назначения...",
        
        # Console
        "console_output": "Консоль",
        "copied": "Скопировано!",
        "copy_tooltip": "Копировать в буфер обмена",
        
        # Combo copy easter egg
        "combo_copy_0": "Скопировано!",
        "combo_copy_1": "Двойное копирование!",
        "combo_copy_2": "Тройное копирование!",
        "combo_copy_3": "Комбо копирование!",
        "combo_copy_4": "Мега копирование!",
        "combo_copy_5": "Супер копирование!",
        "combo_copy_6": "Ультра копирование!",
        "combo_copy_7": "ГИГА КОПИРОВАНИЕ!!!",
        "combo_copy_8": "☆ ЛЕГЕНДАРНОЕ ☆",
        "combo_copy_9": "✦ БОЖЕСТВЕННОЕ ✦",
        "combo_copy_10": "⚡ КОСМИЧЕСКОЕ ⚡",
        "combo_copy_11": "🔥 АПОКАЛИПСИС 🔥",
        "combo_post_0": "Может уже хватит?",
        "combo_post_1": "Серьёзно, прекрати",
        "combo_post_2": "Последнее предупреждение!",
        "combo_post_3": "Кнопка будет отобрана через...",
        "combo_button_gone": "Пока-пока, кнопка! 👋",
        
        # Buttons
        "advanced_options": "Дополнительно...",
        "show_command": "Команда",
        "uat_help": "Справка UAT",
        "clear_console": "Очистить",
        "build_plugin": "Собрать",
        "cancel": "Отмена",
        "ok": "ОК",
        "browse": "Обзор...",
        "add": "Добавить",
        "remove": "Удалить",
        "close": "Закрыть",
        
        # Settings / Engine dialog
        "settings": "Настройки",
        "manage_engine_installations": "Управление движками",
        "registered_engines": "Зарегистрированные движки",
        "double_click_hint": "Двойной клик откроет папку движка",
        "remove_selected": "Удалить выбранное",
        "scan_for_engines": "Поиск движков",
        "add_engine_manually": "Добавить вручную",
        "path_to_ue_installation": "Путь к Unreal Engine...",
        "auto_detect": "Автоопределение...",
        "add_engine": "Добавить движок",
        "path_not_exist": "Путь не существует",
        "not_valid_engine": "Не является установкой Unreal Engine",
        "detected_ue": "Обнаружен UE",
        "valid_engine_unknown_version": "Движок найден, версия неизвестна",
        "engine_added": "Движок добавлен",
        "remove_engine_confirm": "Удалить UE {version} из списка?",
        "version_exists": "UE {version} уже добавлен. Заменить?",
        "version_required": "Укажите версию (например, 5.4)",
        "scanning_engines": "Поиск движков...",
        "found_engines": "Найдено: {count}",
        "found_engines_hint": "Если движки не найдены — добавьте вручную",
        "no_engines_found": "Движки не найдены",
        "folder_not_found": "Папка не существует",
        "could_not_open_folder": "Не удалось открыть папку",
        
        # Advanced options
        "advanced_build_options": "Дополнительные параметры сборки",
        "target_platforms": "Целевые платформы",
        "windows_64": "Windows 64-bit",
        "windows_32": "Windows 32-bit",
        "linux": "Linux",
        "macos": "macOS",
        "build_options": "Параметры сборки",
        "no_host_platform": "Не компилировать для хост-платформы",
        "strict_includes": "Строгие include (без PCH и unity build)",
        "unversioned": "Без версии движка в дескрипторе",
        "additional_parameters": "Дополнительные параметры",
        "additional_params_hint": "Дополнительные параметры командной строки.\nПример: -Param1=Value1 -Flag -Param2=\"Текст\"",
        
        # Command dialog
        "build_command": "Команда сборки",
        "copy_command": "Копировать",
        "command_copied": "Команда скопирована",
        
        # Localization settings
        "language": "Язык",
        "language_settings": "Язык интерфейса",
        "select_language": "Выберите язык",
        "load_custom_locale": "Загрузить локализацию (JSON)",
        "no_custom_locale": "Локализация не загружена",
        "language_restart_note": "Примечание: Для смены языка требуется перезапуск приложения.",
        "locale_loaded": "Локализация загружена",
        "locale_load_error": "Ошибка загрузки локализации",
        "restart_to_apply": "Перезапустите приложение для применения изменений.",
        "select_ue_installation": "Выберите папку Unreal Engine",
        
        # Validation messages
        "validation_error": "Ошибка проверки",
        "select_plugin_file": "Выберите файл плагина.",
        "plugin_not_found": "Файл плагина не найден.",
        "select_target_engine": "Выберите целевой движок.",
        "engine_not_found": "Движок не найден.",
        "specify_output_dir": "Укажите папку назначения.",
        
        # Build messages
        "searching_engines": "Поиск установок Unreal Engine...",
        "found_n_engines": "Найдено движков: {count}",
        "no_engines_add_manually": "Движки не найдены. Добавьте через Настройки.",
        "plugin_selected": "Выбран плагин: {path}",
        "applied_options": "Применены параметры: {options}",
        "build_complete": "Сборка завершена",
        "build_successful": "Плагин собран успешно!\n\nРезультат: {path}",
        "build_failed": "Ошибка сборки",
        "build_failed_msg": "Сборка не удалась:\n\n{error}",
        "build_in_progress": "Идёт сборка",
        "cancel_and_exit": "Сборка в процессе. Отменить и выйти?",
        "error": "Ошибка",
        "generate_command_error": "Не удалось сформировать команду. Проверьте параметры.",
    },
}

# Current language
_current_lang: str = "en"
_custom_translations: Dict[str, str] = {}


def detect_system_language() -> str:
    """Detect system language and return 'ru' if Russian, otherwise 'en'."""
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale and system_locale.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


def get_current_language() -> str:
    """Get current language code."""
    return _current_lang


def set_language(lang: str) -> None:
    """Set current language."""
    global _current_lang
    if lang in _TRANSLATIONS:
        _current_lang = lang
    else:
        _current_lang = "en"


def get_available_languages() -> Dict[str, str]:
    """Get available languages with their display names."""
    return {
        "en": "English",
        "ru": "Русский",
    }


def load_custom_locale(file_path: Path) -> bool:
    """
    Load custom locale from JSON file.
    
    Args:
        file_path: Path to JSON file with translations
        
    Returns:
        True if loaded successfully
    """
    global _custom_translations
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _custom_translations = data
                return True
    except Exception:
        pass
    return False


def clear_custom_locale() -> None:
    """Clear custom locale."""
    global _custom_translations
    _custom_translations = {}


def tr(key: str, **kwargs) -> str:
    """
    Get translated string by key.
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated string
    """
    # Check custom translations first
    if key in _custom_translations:
        text = _custom_translations[key]
    # Then check current language
    elif key in _TRANSLATIONS.get(_current_lang, {}):
        text = _TRANSLATIONS[_current_lang][key]
    # Fall back to English
    elif key in _TRANSLATIONS.get("en", {}):
        text = _TRANSLATIONS["en"][key]
    else:
        # Return key if not found
        return key
    
    # Format with kwargs if any
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def init_localization(saved_language: Optional[str] = None) -> None:
    """
    Initialize localization.
    
    Args:
        saved_language: Previously saved language from config, or None to auto-detect
    """
    global _current_lang
    if saved_language and saved_language in _TRANSLATIONS:
        _current_lang = saved_language
    else:
        _current_lang = detect_system_language()
