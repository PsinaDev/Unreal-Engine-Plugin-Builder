"""
Core data types for UE Plugin Builder.
All types are pure Python dataclasses without Qt dependencies.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path


class BuildStatus(Enum):
    """Status of a build operation."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(Enum):
    """Log message severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class LogMessage:
    """Represents a single log message."""
    text: str
    level: LogLevel = LogLevel.INFO
    timestamp: Optional[str] = None


@dataclass
class ModuleInfo:
    """Information about a plugin module."""
    name: str
    type: str  # Runtime, Editor, Developer, etc.
    loading_phase: str = "Default"
    platform_allow_list: List[str] = field(default_factory=list)
    platform_deny_list: List[str] = field(default_factory=list)


@dataclass
class PluginDependency:
    """Information about a plugin dependency."""
    name: str
    enabled: bool = True
    optional: bool = False
    description: str = ""


@dataclass
class PluginInfo:
    """Information extracted from .uplugin file."""
    # Basic info
    name: str
    friendly_name: str
    version: int
    version_name: str
    description: str
    category: str
    created_by: str
    created_by_url: str
    docs_url: str
    marketplace_url: str
    support_url: str
    
    # Engine info
    engine_version: str
    file_version: int
    
    # Modules
    modules: List[ModuleInfo]
    
    # Dependencies
    plugins: List[PluginDependency]
    
    # Flags
    can_contain_content: bool
    is_beta_version: bool
    is_experimental_version: bool
    installed: bool
    enabled_by_default: bool
    is_hidden: bool
    requires_build_platform: bool
    
    # Platforms
    supported_platforms: List[str]
    
    # File path
    file_path: Path

    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_path: Path) -> "PluginInfo":
        """Create PluginInfo from parsed .uplugin JSON data."""
        # Parse modules
        modules = []
        for m in data.get("Modules", []):
            modules.append(ModuleInfo(
                name=m.get("Name", ""),
                type=m.get("Type", "Runtime"),
                loading_phase=m.get("LoadingPhase", "Default"),
                platform_allow_list=m.get("PlatformAllowList", []),
                platform_deny_list=m.get("PlatformDenyList", []),
            ))
        
        # Parse plugin dependencies
        plugins = []
        for p in data.get("Plugins", []):
            plugins.append(PluginDependency(
                name=p.get("Name", ""),
                enabled=p.get("Enabled", True),
                optional=p.get("Optional", False),
                description=p.get("Description", ""),
            ))
        
        return cls(
            name=file_path.stem,
            friendly_name=data.get("FriendlyName", data.get("Name", file_path.stem)),
            version=data.get("Version", 0),
            version_name=data.get("VersionName", "0.0.0"),
            description=data.get("Description", ""),
            category=data.get("Category", ""),
            created_by=data.get("CreatedBy", ""),
            created_by_url=data.get("CreatedByURL", ""),
            docs_url=data.get("DocsURL", ""),
            marketplace_url=data.get("MarketplaceURL", ""),
            support_url=data.get("SupportURL", ""),
            engine_version=data.get("EngineVersion", ""),
            file_version=data.get("FileVersion", 3),
            modules=modules,
            plugins=plugins,
            can_contain_content=data.get("CanContainContent", False),
            is_beta_version=data.get("IsBetaVersion", False),
            is_experimental_version=data.get("IsExperimentalVersion", False),
            installed=data.get("Installed", False),
            enabled_by_default=data.get("EnabledByDefault", True),
            is_hidden=data.get("bIsHidden", False),
            requires_build_platform=data.get("bRequiresBuildPlatform", False),
            supported_platforms=data.get("SupportedTargetPlatforms", []),
            file_path=file_path,
        )
    
    def get_module_types(self) -> List[str]:
        """Get unique module types."""
        return list(set(m.type for m in self.modules))
    
    def get_module_names(self) -> List[str]:
        """Get module names."""
        return [m.name for m in self.modules]


@dataclass
class EngineInfo:
    """Information about an Unreal Engine installation."""
    version: str
    path: Path
    is_source_build: bool = False
    has_uat: bool = False
    has_editor: bool = False

    @property
    def uat_path(self) -> Path:
        """Get path to RunUAT script."""
        if self.path:
            return self.path / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
        return Path()

    @property
    def editor_path(self) -> Path:
        """Get path to UnrealEditor executable."""
        if self.path:
            ue5_editor = self.path / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe"
            ue4_editor = self.path / "Engine" / "Binaries" / "Win64" / "UE4Editor.exe"
            if ue5_editor.exists():
                return ue5_editor
            return ue4_editor
        return Path()


@dataclass
class BuildConfig:
    """Configuration for a plugin build operation."""
    plugin_path: Path
    output_path: Path
    engine_path: Path
    target_platforms: List[str] = field(default_factory=lambda: ["Win64"])
    no_host_platform: bool = False
    strict_includes: bool = False
    unversioned: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def get_all_params(self) -> Dict[str, Any]:
        """Get all build parameters as a dictionary."""
        params = {}
        
        if self.target_platforms:
            params["TargetPlatforms"] = "+".join(self.target_platforms)
        
        if self.no_host_platform:
            params["NoHostPlatform"] = True
        
        if self.strict_includes:
            params["StrictIncludes"] = True
        
        if self.unversioned:
            params["Unversioned"] = True
        
        params.update(self.extra_params)
        return params


@dataclass
class BuildResult:
    """Result of a build operation."""
    status: BuildStatus
    exit_code: int
    message: str
    duration_seconds: float = 0.0
    output_path: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
