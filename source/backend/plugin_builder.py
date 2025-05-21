import os
import json
import re
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal, QProcess

from source.frontend.localization import LocalizationManager


class PluginBuilderSignals(QObject):
    """
    Signals for PluginBuilder class
    """
    log_message = Signal(str, str)  # (text, type)
    build_started = Signal()
    build_finished = Signal(bool, str)  # (success, message)
    build_progress = Signal(int)  # progress percentage (0-100)


class PluginBuilder:
    """
    Class for building Unreal Engine plugins
    """

    def __init__(self, localization: Optional[LocalizationManager] = None) -> None:
        self.signals = PluginBuilderSignals()
        self.process = None
        self.source_plugin_path = None
        self.output_folder = None
        self.target_engine_path = None
        self.additional_params = {}
        self.localization = localization

    def log(self, message: str, log_type: str = "INFO") -> None:
        """
        Method for logging the build process
        """
        print(f"[{log_type}] {message}")
        self.signals.log_message.emit(message, log_type)

    def extract_plugin_info(self, plugin_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract information from the .uplugin file
        """
        try:
            with open(plugin_path, 'r', encoding='utf-8') as file:
                plugin_data = json.load(file)

            info = {
                "name": plugin_data.get("FriendlyName", "Unknown Plugin"),
                "version": plugin_data.get("Version", 0),
                "description": plugin_data.get("Description", ""),
                "category": plugin_data.get("Category", ""),
                "modules": [m.get("Name") for m in plugin_data.get("Modules", [])],
                "is_engine_plugin": plugin_data.get("EngineVersion", "") != "",
                "engine_version": plugin_data.get("EngineVersion", ""),
                "marketplace_url": plugin_data.get("MarketplaceURL", ""),
                "supported_platforms": plugin_data.get("SupportedTargetPlatforms", []),
            }

            return info
        except Exception as e:
            self.log(f"Error reading plugin information: {e}", "ERROR")
            return None

    def get_build_command(self) -> Optional[List[str]]:
        """
        Create the command for building the plugin
        """
        if not self.source_plugin_path or not self.output_folder or not self.target_engine_path:
            self.log(self.localization("not_all_parameters_set", "Not all required parameters are set for building")
                     if self.localization
                     else "Not all required parameters are set for building", "ERROR")
            return None

        # Form path to RunUAT.bat
        uat_path = os.path.normpath(
            os.path.join(self.target_engine_path, "Engine", "Build", "BatchFiles", "RunUAT.bat"))
        if not os.path.exists(uat_path):
            error_msg = f"RunUAT.bat file not found at path: {uat_path}"
            if self.localization:
                error_msg = self.localization("help_error_uat", error_msg, **{"0": uat_path})
            self.log(error_msg, "ERROR")
            return None

        # Normalize paths to avoid mixing slashes
        source_plugin_path = os.path.normpath(self.source_plugin_path)
        output_folder = os.path.normpath(self.output_folder)

        # Base command
        command = [
            uat_path,
            "BuildPlugin",
            "-plugin",
            source_plugin_path,
            "-package",
            output_folder,
        ]

        # Add additional parameters
        for param, value in self.additional_params.items():
            if value is True:
                command.append(f"-{param}")
            elif value not in (False, None, ""):
                command.append(f"-{param}")
                command.append(str(value))
        return command

    def get_command_string(self) -> str:
        """
        Return string representation of the command
        """
        command = self.get_build_command()
        if not command:
            return ""

        # Format arguments with quotes for paths with spaces
        formatted_command = [command[0]]  # RunUAT.bat
        formatted_command.append(command[1])  # BuildPlugin

        for i in range(2, len(command), 2):
            if i + 1 < len(command):
                # If next argument is a path, add quotes
                param = command[i]
                value = command[i + 1]
                # Normalize path using consistent slashes
                if os.path.exists(os.path.dirname(value)):
                    # Replace all backslashes with forward slashes for consistency
                    value = value.replace("\\", "/")
                    formatted_command.append(f'{param}="{value}"')
                else:
                    formatted_command.append(f'{param}={value}')
            else:
                # If this is the last argument without value
                formatted_command.append(command[i])

        return " ".join(formatted_command)

    def build_plugin(self, source_plugin_path: str, output_folder: str,
                     target_engine_path: str, additional_params: dict = None) -> bool:
        """
        Start building the plugin
        """
        self.source_plugin_path = source_plugin_path
        self.output_folder = output_folder
        self.target_engine_path = target_engine_path
        self.additional_params = additional_params or {}

        # Check if source plugin file exists
        if not os.path.exists(source_plugin_path):
            error_msg = f"Plugin file not found: {source_plugin_path}"
            if self.localization:
                error_msg = self.localization("error_plugin_not_found", error_msg, **{"0": source_plugin_path})
            self.log(error_msg, "ERROR")
            return False

        # Create output folder if it doesn't exist
        try:
            # Check if parent directory is writable
            parent_dir = os.path.dirname(output_folder)
            if not os.access(parent_dir, os.W_OK):
                self.log(f"No permission to create directory in: {parent_dir}", "ERROR")
                return False

            os.makedirs(output_folder, exist_ok=True)
        except (PermissionError, OSError) as e:
            self.log(f"Failed to create output directory: {e}", "ERROR")
            return False

        # Получаем базовую команду
        command = self.get_build_command()
        if not command:
            return False

        # Логируем строковое представление команды
        command_str = self.get_command_string()
        log_msg = f"Build command: {command_str}"
        if self.localization:
            log_msg = self.localization("log_build_command", log_msg, **{"0": command_str})
        self.log(log_msg, "INFO")

        # Start the process
        self.signals.build_started.emit()

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._process_stdout)
        self.process.readyReadStandardError.connect(self._process_stderr)
        self.process.finished.connect(self._process_finished)

        # Формируем параметры в правильном формате, как в get_command_string()
        # Но для QProcess нам нужен список, а не строка
        formatted_args = [command[1]]  # BuildPlugin

        for i in range(2, len(command), 2):
            if i + 1 < len(command):
                # Параметр и значение с "="
                param = command[i]
                value = command[i + 1]

                # Заменяем обратные слеши на прямые
                if os.path.exists(os.path.dirname(value)):
                    value = value.replace("\\", "/")

                # Приводим к формату параметр=значение (без кавычек - QProcess добавит их при необходимости)
                param_name = param.lstrip('-')  # Убираем "-"
                param_name = param_name[0].upper() + param_name[1:]  # Первая буква заглавная
                formatted_args.append(f"-{param_name}={value}")
            else:
                # Просто параметр без значения
                param = command[i].lstrip('-')
                param = param[0].upper() + param[1:]
                formatted_args.append(f"-{param}")

        # Запускаем процесс с правильно отформатированными аргументами
        self.process.start(command[0], formatted_args)

        return True

    def _process_stdout(self) -> None:
        """
        Process standard output from the process
        """
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        for line in data.splitlines():
            line = line.strip()
            if line:
                # Determine message type by content
                log_type = "INFO"
                if re.search(r'error|ошибка|failed', line, re.IGNORECASE):
                    log_type = "ERROR"
                elif re.search(r'warning|предупреждение', line, re.IGNORECASE):
                    log_type = "WARNING"
                elif re.search(r'success|успешно|completed', line, re.IGNORECASE):
                    log_type = "SUCCESS"

                self.log(line, log_type)

                # Try to determine progress
                progress_match = re.search(r'(\d+)%', line)
                if progress_match:
                    progress = int(progress_match.group(1))
                    self.signals.build_progress.emit(progress)

    def _process_stderr(self) -> None:
        """
        Process standard error output from the process
        """
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        for line in data.splitlines():
            line = line.strip()
            if line:
                self.log(line, "ERROR")

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """
        Called when the process finishes
        """
        if exit_code == 0:
            success_msg = "Plugin build completed successfully"
            if self.localization:
                success_msg = self.localization("log_build_success", success_msg)
            self.log(success_msg, "SUCCESS")
            self.signals.build_finished.emit(True, success_msg)
        else:
            error_msg = f"Plugin build failed with error (code: {exit_code})"
            if self.localization:
                error_msg = self.localization("log_build_error", error_msg, **{"0": str(exit_code)})
            self.log(error_msg, "ERROR")
            self.signals.build_finished.emit(False, error_msg)

    def cancel_build(self) -> bool:
        """
        Cancel the current plugin build by terminating the entire process tree,
        waiting for completion before cleanup
        """
        if not self.process or self.process.state() == QProcess.NotRunning:
            return False

        # Получаем PID процесса
        pid = self.process.processId()

        # Завершаем всё дерево процессов через Popen и wait
        import subprocess

        # Сначала убиваем основной процесс и его дочерние процессы
        proc = subprocess.Popen(
            f"taskkill /F /PID {pid} /T",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.wait()  # Ждем завершения команды taskkill

        # Дополнительно убиваем процессы сборки которые могли быть созданы
        build_procs = ["UnrealBuildTool.exe", "UBT.exe"]
        for proc_name in build_procs:
            proc = subprocess.Popen(
                f"taskkill /F /IM {proc_name}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            proc.wait()  # Ждем завершения каждой команды

        # После ожидания завершения всех процессов пытаемся удалить папку
        if self.output_folder and os.path.exists(self.output_folder):
            try:
                import shutil
                shutil.rmtree(self.output_folder, ignore_errors=True)
                self.log(f"Successfully removed folder: {self.output_folder}", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to remove folder: {str(e)}", "WARNING")

        # Логирование и сигнал об отмене
        cancelled_msg = "Plugin build cancelled by user"
        if self.localization:
            cancelled_msg = self.localization("log_build_cancelled", cancelled_msg)
        self.log(cancelled_msg, "WARNING")

        self.signals.build_finished.emit(False, cancelled_msg)
        return True