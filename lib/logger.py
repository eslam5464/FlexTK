import json
import logging
import logging.config
import os.path
import sys
from datetime import datetime, timezone

from core.config import settings
from loguru import logger

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


def configure_logging() -> None:
    """
    This function sets up logging by creating necessary directories,
    modifying configuration files, and applying the logging configuration.
    can be used like below

        >>> logger = logging.getLogger(__name__) # at the top of each script
        >>> logger.info("Test log message") # at any line in the script
    :return: None
    """
    cwd = os.path.dirname(os.path.realpath(__file__))
    logs_folder_directory = os.path.join(cwd, "logs")
    log_file_path = os.path.join(logs_folder_directory, "log.jsonl").replace("\\", "\\\\")
    config_file_path = os.path.join(cwd, "logging_config.json")

    if not os.path.exists(logs_folder_directory):
        os.makedirs(logs_folder_directory, exist_ok=True)

    with open(config_file_path) as config_file:
        config = json.load(config_file)

    config["handlers"]["file_json"]["filename"] = log_file_path
    logging.config.dictConfig(config)


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward loguru sinks.
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2

        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging_new() -> None:
    """
    Configure the logging system for the application
    """
    # Remove default logger
    logger.remove()

    # Log format for console output
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss!UTC}</green> | "
        "<magenta>{process: <6}</magenta> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    log_file_format = "{time:YYYY-MM-DD HH:mm:ss!UTC} | " "{level: <8} | " "{name}:{function}:{line} | " "{message}"

    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    # Add a file handler for more detailed logs
    logger.add(
        f"logs{os.sep}app.log",
        rotation="10 MB",
        retention="1 month",
        compression="zip",
        format=log_file_format,
        level=logging.NOTSET,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set up loggers for FastAPI, Uvicorn, and other libraries
    loggers_to_intercept = [
        "fastapi",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "redis",
    ]

    for logger_name in loggers_to_intercept:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Log the start of the application
    logger.info(f"Logging configured with level {settings.log_level}")
