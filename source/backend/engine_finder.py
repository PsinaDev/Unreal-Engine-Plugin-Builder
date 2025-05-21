import os
import json
import winreg
from typing import Optional, List, Dict
import re
from PySide6.QtCore import QObject, Signal

from source.frontend.localization import LocalizationManager

CONFIG_FILE = "unreal_engines_config.json"


class EngineFinderSignals(QObject):
    """
    Signals for EngineFinder class
    """
    log_message = Signal(str, str)  # (text, type)
    finished = Signal(list)  # List of UE paths
    progress = Signal(int, int)  # (current progress, max progress)


class EngineFinder:
    """
    Class for finding installed Unreal Engine instances
    """
    STANDARD_PATHS = [
        "C:/Program Files/Epic Games",
        "C:/Epic Games",
        os.path.expanduser("~/Epic Games"),
        "D:/Epic Games",
    ]
    REGISTRY_PATHS = [
        r"SOFTWARE\EpicGames\Unreal Engine",
        r"SOFTWARE\EpicGames",
    ]
    POSSIBLE_ENGINE_NAMES = ["Unreal", "UE_", "UE5", "UE4"]

    def __init__(self, localization: Optional[LocalizationManager] = None, config_path: Optional[str] = None) -> None:
        self.config_file = config_path or CONFIG_FILE
        self.signals = EngineFinderSignals()
        self.found_engines = {}  # Dictionary {version: path}
        self.localization = localization

    def log(self, message: str, log_type: str = "INFO") -> None:
        """
        Log method for search process
        """
        print(f"[{log_type}] {message}")
        self.signals.log_message.emit(message, log_type)

    def is_valid_engine_path(self, engine_path: str) -> bool:
        """
        Checks if a path contains a valid Unreal Engine installation

        :param engine_path: Path to check
        :return: True if valid, False otherwise
        """
        # Basic checks for required files and directories
        uat_path = os.path.join(engine_path, "Engine", "Build", "BatchFiles", "RunUAT.bat")
        ue_editor_path = os.path.join(engine_path, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
        ue4_editor_path = os.path.join(engine_path, "Engine", "Binaries", "Win64", "UE4Editor.exe")  # For UE4

        # Check for either UE4Editor.exe or UnrealEditor.exe
        if not os.path.exists(uat_path):
            return False

        # At least one of the editor executables should exist
        has_editor = os.path.exists(ue_editor_path) or os.path.exists(ue4_editor_path)

        # Additional checks for key directories that must be present
        required_dirs = [
            os.path.join(engine_path, "Engine", "Content"),
            os.path.join(engine_path, "Engine", "Plugins"),
            os.path.join(engine_path, "Engine", "Source")
        ]

        dirs_exist = all(os.path.isdir(d) for d in required_dirs)

        return has_editor and dirs_exist

    def find_unreal_in_registry(self) -> List[str]:
        """
        Find paths to Unreal Engine in the registry
        """
        log_msg = self.localization("log_engines_search_start",
                                    "Starting Unreal Engine search...") if self.localization else "Starting Unreal Engine search in registry..."
        self.log(log_msg)
        found_paths = []

        for reg_path in self.REGISTRY_PATHS:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    subkeys_count, _, _ = winreg.QueryInfoKey(key)
                    for i in range(subkeys_count):
                        subkey_name = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                install_path, _ = winreg.QueryValueEx(subkey, "InstalledDirectory")
                                if os.path.exists(install_path) and self.is_valid_engine_path(install_path):
                                    if self.localization:
                                        success_msg = self.localization("log_engine_found_registry",
                                                                        "Unreal Engine found in registry: {0}",
                                                                        **{"0": install_path})
                                    else:
                                        success_msg = f"Unreal Engine found in registry: {install_path}"
                                    self.log(success_msg, "SUCCESS")
                                    found_paths.append(install_path)
                        except FileNotFoundError:
                            continue
            except FileNotFoundError:
                continue

        if not found_paths:
            not_found_msg = self.localization("log_engine_not_found_registry",
                                              "Unreal Engine not found in registry.") if self.localization else "Unreal Engine not found in registry."
            self.log(not_found_msg)

        return found_paths

    def find_unreal_in_env_vars(self) -> List[str]:
        """
        Find paths to Unreal Engine in environment variables
        """
        self.log("Checking environment variables...")
        found_paths = []

        for var in os.environ.values():
            if any(engine_name in var for engine_name in self.POSSIBLE_ENGINE_NAMES):
                if os.path.exists(var) and self.is_valid_engine_path(var):
                    if self.localization:
                        success_msg = self.localization("log_engine_found_env",
                                                        "Unreal Engine found through environment variables: {0}",
                                                        **{"0": var})
                    else:
                        success_msg = f"Unreal Engine found through environment variables: {var}"
                    self.log(success_msg, "SUCCESS")
                    found_paths.append(var)

        if not found_paths:
            not_found_msg = self.localization("log_engine_not_found_env",
                                              "Unreal Engine not found in environment variables.") if self.localization else "Unreal Engine not found in environment variables."
            self.log(not_found_msg)

        return found_paths

    def find_unreal_in_standard_paths(self) -> List[str]:
        """
        Find paths to Unreal Engine in standard locations
        """
        self.log("Searching standard installation paths...")
        found_paths = []

        for base_path in self.STANDARD_PATHS:
            try:
                if os.path.exists(base_path):
                    for subdir in os.listdir(base_path):
                        engine_path = os.path.join(base_path, subdir)
                        if self.is_valid_engine_path(engine_path):
                            if self.localization:
                                success_msg = self.localization("log_engine_found_standard", "Unreal Engine found: {0}",
                                                                **{"0": engine_path})
                            else:
                                success_msg = f"Unreal Engine found: {engine_path}"
                            self.log(success_msg, "SUCCESS")
                            found_paths.append(engine_path)
            except (FileNotFoundError, PermissionError) as e:
                self.log(f"Error accessing {base_path}: {e}", "WARNING")

        if not found_paths:
            not_found_msg = self.localization("log_engine_not_found_standard",
                                              "Unreal Engine not found in standard paths.") if self.localization else "Unreal Engine not found in standard paths."
            self.log(not_found_msg)

        return found_paths

    def extract_version_from_path(self, engine_path: str) -> Optional[str]:
        """
        Extract Unreal Engine version from path
        """
        # Check if path points to the engine root directory
        if not os.path.exists(os.path.join(engine_path, "Engine")):
            if "Engine" in engine_path:
                # If path points to Engine, extract root folder
                engine_path = os.path.dirname(os.path.dirname(engine_path))

        # Look for version in folder name
        version_match = re.search(r'UE_?(\d+\.\d+)', engine_path)
        if version_match:
            return version_match.group(1)

        # Check Build.version file
        version_file = os.path.join(engine_path, "Engine", "Build", "Build.version")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                    major = version_data.get("MajorVersion", 0)
                    minor = version_data.get("MinorVersion", 0)
                    return f"{major}.{minor}"
            except Exception as e:
                self.log(f"Error reading version file: {e}", "WARNING")

        return None

    def save_config(self, engines_data: Dict[str, str]) -> bool:
        """
        Save Unreal Engine paths to configuration file

        Args:
            engines_data: Dictionary mapping engine versions to paths

        Returns:
            bool: True if successful, False otherwise
        """
        config_data = {"unreal_engines": engines_data}

        # Check write permission on directory
        config_dir = os.path.dirname(self.config_file)
        if not os.access(config_dir, os.W_OK):
            self.log(f"No write permission for config directory: {config_dir}", "ERROR")
            return False

        # If file exists, check if we can write to it
        if os.path.exists(self.config_file) and not os.access(self.config_file, os.W_OK):
            self.log(f"No write permission for config file: {self.config_file}", "ERROR")
            return False

        # Now save the file
        try:
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(config_data, file, indent=4)
            self.log(f"Unreal Engine paths saved to {self.config_file}")
            return True
        except IOError as e:
            self.log(f"Error saving engine configuration: {e}", "ERROR")
            return False

    def load_config(self) -> Dict[str, str]:
        """
        Load Unreal Engine paths from configuration file
        """
        check_msg = self.localization("log_config_check",
                                      "Checking configuration file...") if self.localization else "Checking configuration file..."
        self.log(check_msg)

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    config_data = json.load(file)

                    loaded_msg = self.localization("log_config_loaded",
                                                   "Configuration file loaded successfully.") if self.localization else "Configuration file loaded successfully."
                    self.log(loaded_msg)

                    return config_data.get("unreal_engines", {})
            except json.JSONDecodeError as e:
                self.log(f"Error reading configuration file: {e}", "WARNING")
        else:
            not_found_msg = self.localization("log_config_not_found",
                                              "Configuration file not found.") if self.localization else "Configuration file not found."
            self.log(not_found_msg)

        return {}

    def find_all_engines(self, stop_on_first: bool = False, force_rescan: bool = False) -> Dict[str, str]:
        """
        Main function to find all Unreal Engine instances

        :param stop_on_first: If True, stops after finding the first instance
        :param force_rescan: If True, ignores existing config and performs new search
        :return: Dictionary {version: path} of found engines
        """
        self.log("Starting search for installed Unreal Engine instances...")

        # 1. Try loading from configuration file (unless force_rescan is True)
        if not force_rescan:
            saved_engines = self.load_config()
            if saved_engines:
                if self.localization:
                    success_msg = self.localization("log_engines_loaded",
                                                    "Unreal Engine paths loaded from configuration")
                else:
                    success_msg = "Unreal Engine paths loaded from configuration"
                self.log(success_msg, "SUCCESS")

                # Verify paths exist and are valid engines
                valid_engines = {}
                for version, path in saved_engines.items():
                    if os.path.exists(path) and self.is_valid_engine_path(path):
                        valid_engines[version] = path
                    else:
                        self.log(f"Engine version {version} at path {path} is no longer valid or complete", "WARNING")

                if valid_engines:
                    self.found_engines = valid_engines
                    return valid_engines
                else:
                    invalid_msg = self.localization("log_paths_invalid",
                                                    "Saved paths are invalid, performing new search") if self.localization else "Saved paths are invalid, performing new search"
                    self.log(invalid_msg, "WARNING")
        elif force_rescan:
            self.log("Forced rescan requested. Ignoring configuration file.", "INFO")

        all_paths = set()

        # 2. Search in registry
        registry_paths = self.find_unreal_in_registry()
        all_paths.update(registry_paths)
        if stop_on_first and registry_paths:
            return self._process_found_paths([registry_paths[0]])

        # 3. Search in environment variables
        env_paths = self.find_unreal_in_env_vars()
        all_paths.update(env_paths)
        if stop_on_first and env_paths:
            return self._process_found_paths([env_paths[0]])

        # 4. Search in standard paths
        standard_paths = self.find_unreal_in_standard_paths()
        all_paths.update(standard_paths)
        if stop_on_first and standard_paths:
            return self._process_found_paths([standard_paths[0]])

        # 5. If nothing found, notify about the need for manual entry
        if not all_paths:
            self.log(self.localization("quick_search_failed", "Quick search methods failed to find Unreal Engine installations.") if self.localization else "Quick search methods failed to find Unreal Engine installations.", "INFO")
            self.log(self.localization("manual_entry_required", "Manual entry will be required.") if self.localization else "Manual entry will be required.", "INFO")

            # Return empty results - main window will detect this and show dialog
            return {}

        return self._process_found_paths(list(all_paths))

    def _process_found_paths(self, paths: List[str]) -> Dict[str, str]:
        """
        Process found paths, extract versions, and save configuration
        """
        result = {}
        for path in paths:
            version = self.extract_version_from_path(path)
            if version:
                # Normalize path - ensure it points to UE root folder
                normalized_path = path
                if not os.path.exists(os.path.join(path, "Engine")):
                    normalized_path = os.path.dirname(os.path.dirname(path))

                self.log(self.localization("found_engine_version", f"Found Unreal Engine version {version}: {normalized_path}", **{"0": version, "1": normalized_path}) if self.localization else f"Found Unreal Engine version {version}: {normalized_path}", "SUCCESS")
                result[version] = normalized_path

        if result:
            self.save_config(result)
            self.found_engines = result

        return result

