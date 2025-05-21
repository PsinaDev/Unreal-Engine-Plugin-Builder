import os
import json
from PySide6.QtCore import QObject, Signal

# Localization configuration file name
LOCALIZATION_CONFIG_FILE = "localization_config.json"


class LocalizationManager(QObject):
    """
    Application localization manager
    """
    language_changed = Signal(str)  # Signal emitted when language changes

    def __init__(self, config_path=None):
        super().__init__()
        self.config_path = config_path or LOCALIZATION_CONFIG_FILE
        self.current_language = "en"  # Default to English
        self.translations = {
            "ru": {},  # Russian translations
            "en": {}  # English translations
        }

        # Load configuration
        self.load_or_create_config()

    def load_or_create_config(self):
        """
        Load existing configuration or create a new one
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                    self.current_language = config.get("current_language", "en")
                    self.translations = config.get("translations", self.get_default_translations())
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading localization config: {e}")
                self.create_default_config()
        else:
            self.create_default_config()

    def create_default_config(self):
        """
        Create default localization configuration
        """
        self.translations = self.get_default_translations()
        self.save_config()

    def get_default_translations(self):
        """
        Return dictionary with default translations
        """
        return {
            "ru": {
                "main_window_title": "UE Plugin Builder",
                "engine_group": "Unreal Engine",
                "source_version_label": "Исходная версия UE:",
                "target_version_label": "Целевая версия UE:",
                "plugin_group": "Плагин",
                "plugin_file_label": "Выберите .uplugin файл:",
                "plugin_info_label": "Информация о плагине:",
                "plugin_info_empty": "Нет информации. Выберите плагин...",
                "plugin_info_name": "Имя:",
                "plugin_info_version": "Версия:",
                "plugin_info_category": "Категория:",
                "plugin_info_description": "Описание:",
                "plugin_info_modules": "Модули:",
                "plugin_info_engine_version": "Версия движка:",
                "plugin_info_marketplace_url": "URL в Marketplace:",
                "plugin_info_supported_platforms": "Поддерживаемые платформы:",
                "select_uplugin_file": "Выберите файл .uplugin",
                "uplugin_file_filter": "Плагин Unreal (*.uplugin)",
                "select_output_folder": "Выберите папку для сохранения плагина",
                "drop_hint": "Или перетащите папку с плагином сюда",
                "output_group": "Выходной каталог",
                "same_dir_radio": "В родительскую директорию с версией UE",
                "other_dir_radio": "Выбрать другую директорию",
                "advanced_button": "Дополнительные параметры",
                "help_button": "Справка BuildPlugin",
                "clear_console_button": "Очистить консоль",
                "show_command_button": "Показать команду",
                "build_button": "Собрать плагин",
                "abort_button": "Прервать сборку",
                "cancel_build_title": "Отменить сборку?",
                "cancel_build_message": "Вы уверены, что хотите отменить текущую сборку?",
                "cancel_failed": "Нет активного процесса сборки для отмены.",
                "ready_message": "Готов к сборке плагина.",
                "select_plugin_message": "Выберите плагин и параметры сборки, затем нажмите \"Собрать плагин\".",
                "command_dialog_title": "Команда сборки",
                "command_label": "Команда для запуска в командной строке:",
                "error_title": "Ошибка",
                "error_no_plugin": "Не выбран плагин для сборки.",
                "error_plugin_not_found": "Файл плагина не найден: {0}",
                "error_no_output": "Не указан путь для сохранения собранного плагина.",
                "error_no_target_engine": "Не выбрана целевая версия Unreal Engine.",
                "error_cannot_start_build": "Не удалось запустить сборку плагина. Проверьте параметры и логи.",
                "build_running": "Идет сборка...",
                "build_success_title": "Сборка завершена",
                "build_success_message": "Плагин успешно собран в: {0}",
                "plugin_path_placeholder": "Путь к файлу плагина...",
                "plugin_info_error": "Ошибка чтения информации о плагине.",
                "no_engines_warning": "Установки Unreal Engine не добавлены. Пожалуйста, добавьте их через Дополнительные параметры.",
                "build_parameters_group": "Параметры сборки",
                "quick_search_failed": "Быстрый поиск не смог найти установки Unreal Engine.",
                "manual_entry_required": "Потребуется ручной ввод.",
                "found_engine_version": "Найдена версия Unreal Engine {0}: {1}",
                # Advanced options
                "advanced_dialog_title": "Дополнительные параметры",
                "language_settings": "Настройки языка",
                "language_label": "Язык интерфейса:",
                "platforms_label": "Целевые платформы:",
                "options_label": "Опции компиляции:",
                "create_dist_checkbox": "CreateSubFolder (создать подпапку с датой сборки)",
                "no_host_platform_checkbox": "NoHostPlatform (не собирать для хост-платформы)",
                "include_debug_files_checkbox": "IncludeDebugFiles (включить отладочные файлы)",
                "strict_checkbox": "Strict (строгая компиляция)",
                "unversioned_checkbox": "Unversioned (не встраивать версию движка в дескриптор)",
                "extra_params_label": "Дополнительные параметры командной строки:",
                "extra_params_placeholder": "-Param1=Value1 -Param2=Value2",
                "rescan_engines_button": "Пересканировать движки",
                "rescan_title": "Сканирование движков",
                "rescan_message": "Запущено сканирование Unreal Engine.",
                "help_error_engine": "Не удалось получить путь к Unreal Engine.",
                "help_error_target": "Выберите целевую версию Unreal Engine.",
                "help_error_uat": "Не найден файл RunUAT.bat по пути: {0}",
                "help_start": "Получение справки по BuildPlugin...",
                "help_error": "Ошибка при получении справки: {0}",
                "help_header": "=== Справка по BuildPlugin ===",
                "help_footer": "=== Конец справки ===",
                "version_match_warning": "Внимание: Целевая версия совпадает с версией плагина!",
                # Manual engine dialog
                "manual_engines_title": "Добавить установки Unreal Engine",
                "manual_engines_instructions": "Автоматический поиск не обнаружил установок Unreal Engine.\nПожалуйста, добавьте ваши установки Unreal Engine вручную.",
                "manual_engines_edit_instructions": "Управление установками Unreal Engine.\nВы можете добавлять новые установки или удалять существующие.",
                "engine_version_label": "Версия движка:",
                "engine_path_label": "Путь к движку:",
                "engine_version_placeholder": "например, 5.1",
                "engine_path_placeholder": "Путь к Unreal Engine",
                "add_engine_button": "Добавить движок",
                "remove_engine_button": "Удалить выбранный",
                "save_engines_button": "Сохранить и продолжить",
                "cancel_button": "Отмена",
                "select_engine_folder": "Выберите директорию Unreal Engine",
                "error_no_version": "Пожалуйста, введите версию движка.",
                "error_no_path": "Пожалуйста, выберите путь к движку.",
                "invalid_engine_title": "Недействительный путь к движку",
                "invalid_engine_message": "Этот путь не похож на правильную установку Unreal Engine.\nВсё равно добавить его?",
                "engines_added_title": "Движки изменены",
                "engines_added_message": "Установки Unreal Engine были обновлены.",
                "add_engines_button": "Добавить Unreal Engine...",
                # Console logs
                "log_info": "ИНФО",
                "log_error": "ОШИБКА",
                "log_warning": "ПРЕДУПРЕЖДЕНИЕ",
                "log_success": "УСПЕХ",
                "log_engines_search_start": "Начинаю поиск Unreal Engine...",
                "log_engine_found_registry": "Unreal Engine найден в реестре: {0}",
                "log_engine_not_found_registry": "Unreal Engine не найден в реестре.",
                "log_engine_found_env": "Unreal Engine найден через переменные окружения: {0}",
                "log_engine_not_found_env": "Unreal Engine не найден в переменных окружения.",
                "log_engine_found_standard": "Unreal Engine найден: {0}",
                "log_engine_not_found_standard": "Unreal Engine не найден в стандартных путях.",
                "log_searching_disk": "Сканирую диск: {0}",
                "log_engine_found_disk": "Unreal Engine найден на диске {0}: {1}",
                "log_engine_not_found_disk": "Unreal Engine не найден на дисках.",
                "log_config_check": "Проверяю конфигурационный файл...",
                "log_config_loaded": "Конфигурационный файл загружен успешно.",
                "log_config_not_found": "Конфигурационный файл не найден.",
                "log_engines_loaded": "Пути к Unreal Engine загружены из конфигурации",
                "log_paths_invalid": "Сохраненные пути недействительны, выполняется новый поиск",
                "log_engine_not_found": "Unreal Engine не найден.",
                "log_build_start": "Начинаю сборку плагина...",
                "log_build_command": "Команда сборки: {0}",
                "log_build_success": "Сборка плагина успешно завершена",
                "log_build_error": "Сборка плагина завершилась с ошибкой (код: {0})",
                "log_build_cancelled": "Сборка плагина отменена пользователем",
                "language_ru": "Русский",
                "language_en": "English",
                "apply_language": "Применить",
            },
            "en": {
                "main_window_title": "UE Plugin Builder",
                "engine_group": "Unreal Engine",
                "source_version_label": "Source UE Version:",
                "target_version_label": "Target UE Version:",
                "plugin_group": "Plugin",
                "plugin_file_label": "Select .uplugin file:",
                "plugin_info_label": "Plugin Information:",
                "plugin_info_empty": "No information. Please select a plugin...",
                "plugin_info_name": "Name:",
                "plugin_info_version": "Version:",
                "plugin_info_category": "Category:",
                "plugin_info_description": "Description:",
                "plugin_info_modules": "Modules:",
                "plugin_info_engine_version": "Engine Version:",
                "plugin_info_marketplace_url": "Marketplace URL:",
                "plugin_info_supported_platforms": "Supported Platforms:",
                "select_uplugin_file": "Select .uplugin file",
                "uplugin_file_filter": "Unreal Plugin (*.uplugin)",
                "select_output_folder": "Select folder to save plugin",
                "drop_hint": "Or drag & drop plugin folder here",
                "output_group": "Output Directory",
                "same_dir_radio": "To parent directory",
                "other_dir_radio": "Select another directory",
                "advanced_button": "Advanced Options",
                "help_button": "BuildPlugin Help",
                "clear_console_button": "Clear Console",
                "show_command_button": "Show Command",
                "build_button": "Build Plugin",
                "abort_button": "Cancel Build",
                "cancel_build_title": "Cancel Build?",
                "cancel_build_message": "Are you sure you want to cancel the current build?",
                "cancel_failed": "No active build process to cancel.",
                "ready_message": "Ready to rebuild plugin.",
                "select_plugin_message": "Select plugin and build parameters, then click \"Rebuild Plugin\".",
                "command_dialog_title": "Build Command",
                "command_label": "Command to run in command line:",
                "error_title": "Error",
                "error_no_plugin": "No plugin selected for build.",
                "error_plugin_not_found": "Plugin file not found: {0}",
                "error_no_output": "Output path not specified.",
                "error_no_target_engine": "Target Unreal Engine version not selected.",
                "error_cannot_start_build": "Failed to start plugin build. Check parameters and logs.",
                "build_running": "Building...",
                "build_success_title": "Build Complete",
                "build_success_message": "Plugin successfully built to: {0}",
                "plugin_path_placeholder": "Path to plugin file...",
                "plugin_info_error": "Error reading plugin information.",
                "no_engines_warning": "No Unreal Engine installations added. Please add engines via Advanced Options.",
                "build_parameters_group": "Build Parameters",
                "quick_search_failed": "Quick search methods failed to find Unreal Engine installations.",
                "manual_entry_required": "Manual entry will be required.",
                "found_engine_version": "Found Unreal Engine version {0}: {1}",
                "version_match_warning": "Warning: Target version matches plugin version!",
                # Advanced options
                "advanced_dialog_title": "Advanced Options",
                "language_settings": "Language Settings",
                "language_label": "Interface Language:",
                "platforms_label": "Target Platforms:",
                "options_label": "Build Options:",
                "create_dist_checkbox": "CreateSubFolder (create subfolder with build date)",
                "no_host_platform_checkbox": "NoHostPlatform (do not build for host platform)",
                "include_debug_files_checkbox": "IncludeDebugFiles (include debug files)",
                "strict_checkbox": "Strict (strict compilation)",
                "unversioned_checkbox": "Unversioned (do not embed engine version in descriptor)",
                "extra_params_label": "Additional command line parameters:",
                "extra_params_placeholder": "-Param1=Value1 -Param2=Value2",
                "rescan_engines_button": "Rescan Engines",
                "rescan_title": "Scanning Engines",
                "rescan_message": "Unreal Engine scanning started.",
                "help_error_engine": "Failed to get Unreal Engine path.",
                "help_error_target": "Select target Unreal Engine version.",
                "help_error_uat": "RunUAT.bat file not found at path: {0}",
                "help_start": "Getting BuildPlugin help...",
                "help_error": "Error getting help: {0}",
                "help_header": "=== BuildPlugin Help ===",
                "help_footer": "=== End of Help ===",
                # Manual engine dialog text
                "manual_engines_title": "Add Unreal Engine Installations",
                "manual_engines_instructions": "Automatic search didn't find any Unreal Engine installations.\nPlease add your Unreal Engine installations manually.",
                "manual_engines_edit_instructions": "Manage your Unreal Engine installations below.\nYou can add new installations or remove existing ones.",
                "engine_version_label": "Engine Version:",
                "engine_path_label": "Engine Path:",
                "engine_version_placeholder": "e.g. 5.1",
                "engine_path_placeholder": "Path to Unreal Engine",
                "add_engine_button": "Add Engine",
                "remove_engine_button": "Remove Selected",
                "save_engines_button": "Save and Continue",
                "cancel_button": "Cancel",
                "select_engine_folder": "Select Unreal Engine Directory",
                "error_no_version": "Please enter an engine version.",
                "error_no_path": "Please select an engine path.",
                "invalid_engine_title": "Invalid Engine Path",
                "invalid_engine_message": "This doesn't appear to be a valid Unreal Engine installation.\nDo you want to add it anyway?",
                "engines_added_title": "Engines Modified",
                "engines_added_message": "Unreal Engine installations have been updated.",
                "add_engines_button": "Add Unreal Engine...",
                # Console logs
                "log_info": "INFO",
                "log_error": "ERROR",
                "log_warning": "WARNING",
                "log_success": "SUCCESS",
                "log_engines_search_start": "Starting Unreal Engine search...",
                "log_engine_found_registry": "Unreal Engine found in registry: {0}",
                "log_engine_not_found_registry": "Unreal Engine not found in registry.",
                "log_engine_found_env": "Unreal Engine found through environment variables: {0}",
                "log_engine_not_found_env": "Unreal Engine not found in environment variables.",
                "log_engine_found_standard": "Unreal Engine found: {0}",
                "log_engine_not_found_standard": "Unreal Engine not found in standard paths.",
                "log_searching_disk": "Scanning disk: {0}",
                "log_engine_found_disk": "Unreal Engine found on disk {0}: {1}",
                "log_engine_not_found_disk": "Unreal Engine not found on disks.",
                "log_config_check": "Checking configuration file...",
                "log_config_loaded": "Configuration file loaded successfully.",
                "log_config_not_found": "Configuration file not found.",
                "log_engines_loaded": "Unreal Engine paths loaded from configuration",
                "log_paths_invalid": "Saved paths are invalid, performing new search",
                "log_engine_not_found": "Unreal Engine not found.",
                "log_build_start": "Starting plugin build...",
                "log_build_command": "Build command: {0}",
                "log_build_success": "Plugin build completed successfully",
                "log_build_error": "Plugin build failed with error (code: {0})",
                "log_build_cancelled": "Plugin build cancelled by user",
                "language_ru": "Русский",
                "language_en": "English",
                "apply_language": "Apply",
            }
        }

    def save_config(self) -> bool:
        """
        Save configuration to file
        """
        config = {
            "current_language": self.current_language,
            "translations": self.translations
        }

        config_dir = os.path.dirname(self.config_path)
        if not os.access(config_dir, os.W_OK):
            return False

        # If file exists, check if we can write to it
        if os.path.exists(self.config_path) and not os.access(self.config_path, os.W_OK):
            return False

        # Now save the file
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            return False

    def set_language(self, language_code):
        """
        Set application language
        """
        if language_code in self.translations:
            self.current_language = language_code
            self.save_config()
            self.language_changed.emit(language_code)

    def get_translation(self, key, default=None, **kwargs):
        """
        Return translation for a key
        """
        translation = self.translations.get(self.current_language, {}).get(key, default or key)

        # Replace parameters in the string
        if kwargs:
            try:
                # First try: Direct keyword replacement with native kwargs
                translation = translation.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                try:
                    # Second try: Convert numeric string keys to positional args
                    # This handles cases where kwargs are {"0": value} but format string is {0}
                    positional_args = []
                    for i in range(10):  # Support up to 10 numeric args
                        str_key = str(i)
                        if str_key in kwargs:
                            positional_args.append(kwargs[str_key])

                    if positional_args:
                        translation = translation.format(*positional_args)
                except (KeyError, ValueError, IndexError):
                    # If all else fails, return unformatted translation
                    pass

        return translation

    def __call__(self, key, default=None, **kwargs):
        """
        Allow using the instance as a function
        """
        return self.get_translation(key, default, **kwargs)