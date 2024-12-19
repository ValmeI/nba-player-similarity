import sys
import traceback
from typing import Optional, Type
from types import TracebackType
from loguru import logger
import os


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def setup_loguru_logger() -> None:
    logger.remove()
    project_root = get_project_root()
    logs_folder_name = "logs"
    file_log_name = "spend_search_backend.log"
    log_file_path = os.path.join(project_root, logs_folder_name, file_log_name)
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS ZZ}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>{exception}"
    )

    logger.add(log_file_path, rotation="00:00", level="INFO", format=log_format, backtrace=True, diagnose=True)
    logger.add(sys.stderr, level="INFO", format=log_format, colorize=True, backtrace=True, diagnose=True)


def handle_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:
    """Global exception handler to catch and log any uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    traceback_string = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        logger.error(
            f"An unhandled exception occurred: {exc_type.__name__}: {exc_value}, traceback: {traceback_string}"
        )
    except Exception:
        # If logger is not available or fails, fall back to printing
        sys.stderr.write("Logging failed. Printing error directly:\n")
        sys.stderr.write(f"Unhandled exception: {exc_type.__name__}: {exc_value}\n{traceback_string}\n")


sys.excepthook = handle_exception
setup_loguru_logger()
