"""
UE Plugin Builder - Core Module

This module contains the business logic without any Qt dependencies.
Can be used for both GUI and headless/CLI operations.
"""

from .types import (
    BuildStatus,
    LogLevel,
    LogMessage,
    PluginInfo,
    ModuleInfo,
    PluginDependency,
    EngineInfo,
    BuildConfig,
    BuildResult,
)

from .platform_utils import (
    get_platform,
    platform_handler,
    PlatformHandler,
)

from .config import (
    AppConfig,
    ConfigManager,
    get_config_manager,
)

from .engine_finder import EngineFinder

from .plugin_builder import (
    PluginBuilder,
    parse_extra_params,
)

from .localization import (
    tr,
    get_current_language,
    set_language,
    get_available_languages,
    load_custom_locale,
    clear_custom_locale,
    init_localization,
    detect_system_language,
)


__all__ = [
    # Types
    "BuildStatus",
    "LogLevel",
    "LogMessage",
    "PluginInfo",
    "ModuleInfo",
    "PluginDependency",
    "EngineInfo",
    "BuildConfig",
    "BuildResult",
    # Platform
    "get_platform",
    "platform_handler",
    "PlatformHandler",
    # Config
    "AppConfig",
    "ConfigManager",
    "get_config_manager",
    # Engine
    "EngineFinder",
    # Builder
    "PluginBuilder",
    "parse_extra_params",
    # Localization
    "tr",
    "get_current_language",
    "set_language",
    "get_available_languages",
    "load_custom_locale",
    "clear_custom_locale",
    "init_localization",
    "detect_system_language",
]
