"""This module implements a specific logging API for simulations."""

import logging

__all__ = ["log_to_console", "log_to_file", "set_log_level",
           "remove_console_log", "debug", "info", "warning", "error", "critical"]


class ColorFormatter(logging.Formatter):
    """Class used to format log output color depending on its level.

    DEBUG: blue
    INFO: grey
    WARNING: yellow
    ERROR: red
    CRITICAL: bold red

    Parameters
    ----------
    fmt : str, optional
        The text format to apply to the log entry. Defaults to the message alone.
    """

    grey = '\x1b[37m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt="%(message)s"):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.grey + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("QI_Logger")
logger.setLevel(logging.DEBUG)


def log_to_console(level=logging.DEBUG):
    r"""Activate log output to the stdout console.

    Parameters
    ----------
    level : int, optional
        The logging level for the console. Defaults to logging.DEBUG

    Returns
    -------
    :class:`logging.StreamHandler`
        The handler of the log output.
    """
    ch = logging.StreamHandler()
    level = sanitize_log_level(level)
    ch.setLevel(level)
    ch.setFormatter(ColorFormatter())
    remove_console_log()  # to avoid double log on console if user calls this function twice
    logger.addHandler(ch)
    return ch


def log_to_file(filename, level=logging.DEBUG):
    r"""Activate log output to the specified file.

    Parameters
    ----------
    filename : str
        The name of the output log file. If not present it is created. It is opened in append mode.
    level : int, optional
        The logging level on the file. Defaults to `logging.DEBUG`

    Returns
    -------
    :class:`logging.FileHandler`
        The handler of the log output.
    """
    fh = logging.FileHandler(filename=filename)
    level = sanitize_log_level(level)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(''))
    logger.addHandler(fh)
    return fh


def set_log_level(level):
    r"""Set the log level on all outputs.

    Parameters
    ----------
    level : int
        The new log level. Can be one of the following:
        - logging.DEBUG === "DEBUG" === 0
        - logging.INFO === "INFO" === 1 
        - logging.WARNING === "WARNING" === 2
        - logging.ERROR === "ERROR" === 3
        - logging.CRITICAL === "CRITICAL" === 4
    """

    level = sanitize_log_level(level)

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def remove_console_log():
    """Remove the console log handler."""
    h = None
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            h = handler
            break
    if h is not None:
        logger.removeHandler(h)


def sanitize_log_level(level):

    if isinstance(level, str):
        level = level.upper()
        if level == "DEBUG":
            level = logging.DEBUG
        elif level == "INFO":
            level = logging.INFO
        elif level == "WARNING":
            level = logging.WARNING
        elif level == "ERROR":
            level = logging.ERROR
        elif level == "CRITICAL":
            level = logging.CRITICAL
        else:
            raise ValueError(f"Invalid log level: {level}")

    return level


def debug(message, module_id=None, time=None):
    r"""Log a message with level DEBUG on the logger.

    Parameters
    ----------
    message : str
        The message to be logged. It should not contain the current simulation time because it is already
        present in the log format.
    module_id : int or str or None optional
        If not ``None``, an additional string is added to the log entry, containing the module identifier (or its name).
    time : int or float or None, optional
        If not ``None``, an additional string is added to the log entry, containing the current simulation time.
    """
    log_message = ""
    if time is not None:
        if int(time) == time:
            log_message = f"[{int(time)}]::"
        else:
            log_message = f"[{time:.3f}]::"

    log_message += "DEBUG::"
    if module_id is not None:
        log_message += f"MODULE-{module_id}::"
    log_message += (" " + message)
    logger.debug(log_message)


def info(message, module_id=None, time=None):
    r"""Log a message with level INFO on the logger.

    Parameters
    ----------
    message : str
        The message to be logged. It should not contain the current simulation time because it is already
        present in the log format.
    module_id : int or str or None optional
        If not ``None``, an additional string is added to the log entry, containing the module identifier (or its name).
    time : int or float or None, optional
        If not ``None``, an additional string is added to the log entry, containing the current simulation time.
    """
    log_message = ""
    if time is not None:
        log_message = f"[{time}]::"

    log_message += "INFO::"
    if module_id is not None:
        log_message += f"MODULE-{module_id}::"
    log_message += (" " + message)
    logger.info(log_message)


def warning(message, module_id=None, time=None):
    r"""Log a message with level WARNING on the logger.

    Parameters
    ----------
    message : str
        The message to be logged. It should not contain the current simulation time because it is already
        present in the log format.
    module_id : int or str or None optional
        If not ``None``, an additional string is added to the log entry, containing the module identifier (or its name).
    time : int or float or None, optional
        If not ``None``, an additional string is added to the log entry, containing the current simulation time.
    """
    log_message = ""
    if time is not None:
        log_message = f"[{time}]::"

    log_message += "WARNING::"
    if module_id is not None:
        log_message += f"MODULE-{module_id}::"
    log_message += (" " + message)
    logger.warning(log_message)


def error(message, module_id=None, time=None):
    """Log a message with level ERROR on the logger.

    Parameters
    ----------
    message : str
        The message to be logged. It should not contain the current simulation time because it is already
        present in the log format.
    module_id : int or str or None optional
        If not ``None``, an additional string is added to the log entry, containing the module identifier (or its name).
    time : int or float or None, optional
        If not ``None``, an additional string is added to the log entry, containing the current simulation time.
    """
    log_message = ""
    if time is not None:
        log_message = f"[{time}]::"

    log_message += "ERROR::"
    if module_id is not None:
        log_message += f"MODULE-{module_id}::"
    log_message += (" " + message)
    logger.error(log_message)


def critical(message, module_id=None, time=None):
    """Log a message with level CRITICAL on the logger.

    Parameters
    ----------
    message : str
        The message to be logged. It should not contain the current simulation time because it is already
        present in the log format.
    module_id : int or str or None optional
        If not ``None``, an additional string is added to the log entry, containing the module identifier (or its name).
    time : int or float or None, optional
        If not ``None``, an additional string is added to the log entry, containing the current simulation time.
    """
    log_message = ""
    if time is not None:
        log_message = f"[{time}]::"

    log_message += "CRITICAL::"
    if module_id is not None:
        log_message += f"MODULE-{module_id}::"
    log_message += (" " + message)
    logger.critical(log_message)
