# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
# ----------------------------------------------------------------------------
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper functions to manage QApplication"""

__all__ = ["getApplication"]

import logging

from qarbon.external.qt import QtGui


def getApplication(argv=None, **properties):
    """Returns a QApplication.
    If the process has initialized before a QApplication it returns the
    existing instance, otherwise it creates a new one

    :param argv: optional arguments to QApplication. If the QApplication is
                 already initialized, argv will have no effect
    :return: the QApplication
    :rtype: QtGui.QApplication"""

    app = QtGui.QApplication.instance()
    if app is None:
        if argv is None:
            from sys import argv
        app = QtGui.QApplication(argv)
    elif argv:
        logging.info("QApplication already initialized. argv will have "
                     "no effect")
    return app

Application = getApplication
