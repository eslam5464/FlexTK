import json
import logging
import logging.config
import os.path
from copy import deepcopy
from datetime import datetime, timezone

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class MyJSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for logging.
    :param fmt_keys: dict[str, str] | None - Optional dictionary to map log record attributes to custom keys.
    """

    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record and returns it as a JSON string.
        :param record: logging.LogRecord - The log record to format.
        :return: str - The formatted log record as a JSON string.
        """
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord) -> dict[str, str | None]:
        """
        Prepares a dictionary representation of a log record.
        :param record: logging.LogRecord - The log record to process.
        :return: dict - The dictionary representation of the log record.
        """
        always_fields = {
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message: dict[str, str | None] = {
            key: (msg_val if (msg_val := always_fields.pop(val, None)) is not None else getattr(record, val))
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message


def replace_log_directory_name(
    file_location: str,
    old_string: str,
    new_string: str,
) -> None:
    """
    Replaces occurrences of a string in a file with a new string.
    :param file_location: str - The path to the file to modify.
    :param old_string: str - The string to replace.
    :param new_string: str - The replacement string.
    :return: None
    """
    with open(file_location, "r") as log_file:
        file_data = log_file.read()

    with open(file_location, "w") as log_file:
        file_data = file_data.replace(old_string, new_string)
        log_file.write(file_data)


def configure_logging() -> None:
    """
    This function sets up logging by creating necessary directories,
    modifying configuration files, and applying the logging configuration.
    can be used like below

        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Test log message")
    :return: None
    """
    cwd = os.path.dirname(os.path.realpath(__file__))
    logs_folder_directory = os.path.join(cwd, "logs")
    log_file_path = os.path.join(logs_folder_directory, "log.jsonl").replace(
        "\\",
        "\\\\",
    )
    config_file_path = os.path.join(cwd, "logging_config.json")
    logger_dict = deepcopy(logging.root.manager.loggerDict)
    logging.root.manager.loggerDict = logger_dict

    if not os.path.exists(logs_folder_directory):
        os.mkdir(logs_folder_directory)

    replace_log_directory_name(
        file_location=config_file_path,
        old_string="LOG_FILE_DIRECTORY",
        new_string=log_file_path,
    )

    with open(config_file_path) as config_file:
        config = json.load(config_file)

    replace_log_directory_name(
        file_location=config_file_path,
        new_string="LOG_FILE_DIRECTORY",
        old_string=log_file_path,
    )

    logging.config.dictConfig(config)
