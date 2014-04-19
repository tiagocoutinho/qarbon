# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper logging functions."""

__all__ = ["log", "debug", "info", "warn", "warning", "error", "exception",
           "fatal", "critical", "initialize", "is_initialized",
           "log_it", "debug_it", "info_it", "warn_it", "error_it", "fatal_it"]

import inspect
import logging
import warnings
import functools


from qarbon import config
from qarbon.util import isString

__logging_initialized = False


def log(level, msg, *args, **kwargs):
    exc_info = kwargs.get('exc_info')
    if exc_info is not None and isString(exc_info):
        kwargs.pop('exc_info')
        exc_info = exc_info.upper()
        logging.log(level, msg, *args, **kwargs)
        exc_level = getattr(logging, exc_info, level)
        logging.log(exc_level, "Exception details:", exc_info=1)
    else:    
        logging.log(level, msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    log(logging.DEBUG, msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    log(logging.INFO, msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    log(logging.WARN, msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    log(logging.WARNING, msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    log(logging.ERROR, msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    if 'exc_info' not in kwargs:
        kwargs['exc_info'] = 1
    error(msg, *args, **kwargs)


def fatal(msg, *args, **kwargs):
    log(logging.FATAL, msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    log(logging.CRITICAL, msg, *args, **kwargs)


def is_initialized():
    return __logging_initialized


def initialize(log_level=None, log_format=None, stream=None,
               file_name=None, file_size=None, file_number=None):
    """Initializes logging. Configures the Root logger with the given
    log_level. If file_name is given, a rotating log file handler is added.
    Otherwise, adds a default output stream handler with the given
    log_format."""

    global __logging_initialized

    if __logging_initialized:
        return

    root = logging.getLogger()
    if log_level is None:
        log_level = config.LOG_LEVEL
    if log_format is None:
        log_format = config.LOG_FORMAT
    if file_name is None:
        file_name = config.LOG_FILE_NAME
    if file_size is None:
        file_size = config.LOG_FILE_SIZE
    if file_number is None:
        file_number = config.LOG_FILE_NUMBER
    if stream is None:
        stream = config.LOG_STREAM

    for handler in set(root.handlers):
        root.removeHandler(handler)

    __set_log_file(file_name, file_size, file_number, log_format)

    __set_log_stream(stream, log_format)

    if isString(log_level):
        log_level = log_level.upper()
        if hasattr(logging, log_level):
            log_level = getattr(logging, log_level)

    if log_level is not None:
        try:
            root.setLevel(log_level)
        except:
            warnings.warn('Invalid log level specified in ' \
                          'qarbon.util.initLogging')

    __logging_initialized = True


def __config_handler(handler, log_format):
    root = logging.getLogger()

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    root.addHandler(handler)


def __set_log_stream(stream, log_format):
    if stream and log_format:
        out_handler = logging.StreamHandler(stream)
        __config_handler(out_handler, log_format)


def __set_log_file(file_name, file_size, file_number, log_format):
    if file_name and file_size and file_number and log_format:
        file_handler = logging.handlers.RotatingFileHandler(file_name, 'a',
                                                        file_size, file_number)
        __config_handler(file_handler, log_format)


def __log_it(obj=None, **kwargs):
    """Log decorator. Use it to decorate any method, function or class. It will
    report to the logging system when the function is called and when the
    function exits.

        :param obj: callable / class to be decorated
        :param logger: [default: None, means use root logger]
        :param log_level: [default: logging.INFO]
        :param show_args: [default: False]
        :param show_kwargs: [default:False]
        :param log_in: log message when entering function [default: True]
        :param log_out: log message when leaving function [default: True]"""

    if obj is None:
        return functools.partial(__log_it, **kwargs)
    elif isinstance(obj, type):
        # treat class
        for key in dir(obj):
            if key.startswith('__'):
                continue
            val = getattr(obj, key)
            if callable(val):
                setattr(obj, key, __log_it(val, **kwargs))
        return obj

    if not callable(obj):
        raise TypeError('{!r} is not a callable object'.format(obj))

    # determine the object name
    name = obj.__name__
    if hasattr(obj, "__qualname__"):
        name = obj.__qualname__  # [class.]function
    else:
        if inspect.ismethod(obj):
            name = obj.im_class.__name__ + "." + name

    # determine the log object
    log_obj = kwargs.get('logger', None)
    if log_obj is None:
        if inspect.ismethod(obj):
            log_obj = logging.getLogger(obj.im_class.__name__)
        else:
            log_obj = logging.getLogger()
    elif isinstance(log_obj, str):
        log_obj = logging.getLogger(log_obj)
    elif isinstance(log_obj, logging.Logger):
        pass
    else:
        log_obj = logging.getLogger()
    log_level = kwargs.get('log_level', logging.INFO)
    log_f = functools.partial(log_obj.log, log_level)

    #TODO: implement the show_args and show_kwargs
    #show_args = kwargs.get('show_args', False)
    #show_kwargs = kwargs.get('show_kwargs', False)

    log_in = kwargs.get('log_in', True)
    log_out = kwargs.get('log_out', True)

    @functools.wraps(obj)
    def wrapper(*w_args, **w_kwargs):
        if log_in:
            log_f("[ IN] %s()", name)
        exc_ocurred = True
        try:
            result = obj(*w_args, **w_kwargs)
            exc_ocurred = False
        finally:
            if log_out:
                exc_msg, exc_info = '[OUT]', False
                if exc_ocurred:
                    exc_msg = '[EXC]'
                log_f("%s %s()", exc_msg, name, exc_info=exc_info)
        return result
    return wrapper

log_it = __log_it(log_level=logging.INFO)
debug_it = __log_it(log_level=logging.DEBUG)
info_it = __log_it(log_level=logging.INFO)
warn_it = __log_it(log_level=logging.WARNING)
error_it = __log_it(log_level=logging.ERROR)
critical_it = __log_it(log_level=logging.CRITICAL)
fatal_it = __log_it(log_level=logging.fatal)
