# -*- coding: utf-8 -*-

##############################################################################
##
## This file is part of qarbon
##
## http://www.qarbon.org/
##
## Copyright 2013 European Synchrotron Radiation Facility, Grenoble, France
##
## qarbon is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## qarbon is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with qarbon.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""Helper classes to manage Qt styles and stylesheets"""

from qarbon.qt.gui.application import getApplication


def getStyle():
    """Returns the current active application style

    :return: the current active application style
    :rtype: QtGui.QStyle"""
    return getApplication().style()
