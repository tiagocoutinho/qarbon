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

from __future__ import print_function

import sys
import time

from qarbon import config
from qarbon import log
from qarbon.tango import Factory

def main():
    config.EXECUTOR = "thread"
    config.MAX_WORKERS = 1
    
    log.initialize(log_level='debug')
    log.info("Started tango console client. Press Ctrl+C at any time to exit")

    attr_name = 'sys/tg_test/1/double_scalar'
    if len(sys.argv) > 1:
        attr_name = sys.argv[1]

    f = Factory()
    attr = f.get_attribute(attr_name)

    #@log.info_it
    def value_changed(new_value):
        log.info("Event: %s %s", new_value.label, new_value)
    attr.valueChanged.connect(value_changed)

    v = attr.read()
    log.info("Read: %s: %s", v.label, v)

    log.info("\nAttribute str: %s\nAttribute repr: %r", attr, attr)
    log.info("\nDevice str: %s\nDevice repr: %r", attr.device, attr.device)
    log.info("\nDatabase str: %s\nDatabase repr: %r", attr.device.database,
             attr.device.database)

    nap = 5
    log.info("Waiting for %fs and then delete the one and only (hopefully) "
             "reference to attr...", nap)
    time.sleep(nap)

    
    del attr
    log.info("Deleted what was hopefully the last reference to attr. You "
             "should't see anymore events")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
