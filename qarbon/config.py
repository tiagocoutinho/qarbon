# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Global configuration."""

import sys

#: qarbon namespace
NAMESPACE = "qarbon"

# ----------------------------------------------------------------------------
# Qt configuration
# ----------------------------------------------------------------------------

#: Auto initialize Qt
DEFAULT_QT_AUTO_INIT = True

#: Set preffered API if not is already loaded
DEFAULT_QT_AUTO_API = 'PyQt4'

#: Whether or not should be strict in choosing Qt API
DEFAULT_QT_AUTO_STRICT = False

#: Auto initialize Qt logging to python logging
DEFAULT_QT_AUTO_INIT_LOG = True

#: Auto initialize Qarbon resources (icons)
DEFAULT_QT_AUTO_INIT_RES = True

#: Remove input hook (only valid for PyQt4)
DEFAULT_QT_AUTO_REMOVE_INPUTHOOK = True


#: Auto initialize Qt
QT_AUTO_INIT = DEFAULT_QT_AUTO_INIT

#: Set preffered API if not is already loaded
QT_AUTO_API = DEFAULT_QT_AUTO_API

#: Whether or not should be strict in choosing Qt API
QT_AUTO_STRICT = DEFAULT_QT_AUTO_STRICT

#: Auto initialize Qt logging to python logging
QT_AUTO_INIT_LOG = DEFAULT_QT_AUTO_INIT_LOG

#: Auto initialize Qarbon resources (icons)
QT_AUTO_INIT_RES = DEFAULT_QT_AUTO_INIT_RES

#: Remove input hook (only valid for PyQt4)
QT_AUTO_REMOVE_INPUTHOOK = DEFAULT_QT_AUTO_REMOVE_INPUTHOOK


# ----------------------------------------------------------------------------
# logging configuration
# ----------------------------------------------------------------------------

DEFAULT_LOG_LEVEL = 'WARNING'
DEFAULT_LOG_FORMAT = \
    '%(threadName)-10s %(levelname)-7s %(asctime)s %(name)s: %(message)s'
DEFAULT_LOG_STREAM = sys.stderr
DEFAULT_LOG_FILE_NAME = None
DEFAULT_LOG_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_LOG_FILE_NUMBER = 100

LOG_LEVEL = DEFAULT_LOG_LEVEL
LOG_FORMAT = DEFAULT_LOG_FORMAT

LOG_STREAM = DEFAULT_LOG_STREAM
LOG_FILE_NAME = DEFAULT_LOG_FILE_NAME
LOG_FILE_SIZE = DEFAULT_LOG_FILE_SIZE
LOG_FILE_NUMBER = DEFAULT_LOG_FILE_NUMBER

# ----------------------------------------------------------------------------
# Paralelism
# ----------------------------------------------------------------------------

DEFAULT_EXECUTOR = 'thread' # possible values 'thread', 'process', 'gevent'

DEFAULT_MAX_WORKERS = 10

EXECUTOR = DEFAULT_EXECUTOR

MAX_WORKERS = DEFAULT_MAX_WORKERS

