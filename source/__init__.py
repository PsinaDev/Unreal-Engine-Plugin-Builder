"""
UE Plugin Builder

A modular tool for building Unreal Engine plugins.
Can be used as:
- Standalone GUI application
- Python module for headless/programmatic use
- CLI tool

Example usage (headless):
    from ue_plugin_builder import PluginBuilder, BuildConfig, EngineFinder
    
    finder = EngineFinder()
    engines = finder.find_all_engines()
    
    builder = PluginBuilder(log_callback=print)
    config = BuildConfig(
        plugin_path=Path("MyPlugin.uplugin"),
        output_path=Path("Output"),
        engine_path=engines["5.4"].path,
    )
    result = builder.build_plugin(config, blocking=True)

Example usage (GUI):
    from ue_plugin_builder.app import main
    main()
"""

__version__ = "1.0.0"
__author__ = "Kim"

# Re-export core types and classes for convenience
from .core import (
    # Types
    BuildStatus,
    LogLevel,
    LogMessage,
    PluginInfo,
    EngineInfo,
    BuildConfig,
    BuildResult,
    # Platform
    get_platform,
    platform_handler,
    # Config
    AppConfig,
    ConfigManager,
    get_config_manager,
    # Engine
    EngineFinder,
    # Builder
    PluginBuilder,
    parse_extra_params,
)


__all__ = [
    # Version
    "__version__",
    "__author__",
    # Types
    "BuildStatus",
    "LogLevel",
    "LogMessage",
    "PluginInfo",
    "EngineInfo",
    "BuildConfig",
    "BuildResult",
    # Platform
    "get_platform",
    "platform_handler",
    # Config
    "AppConfig",
    "ConfigManager",
    "get_config_manager",
    # Engine
    "EngineFinder",
    # Builder
    "PluginBuilder",
    "parse_extra_params",
]
