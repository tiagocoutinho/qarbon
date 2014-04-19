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

"""Executor."""

__all__ = ["Executor", "submit", "task", "map", "shutdown"]

import sys
from concurrent import futures


class SerialExecutor(futures.Executor):

    def __init__(self, *args, **kwargs):
        pass

    def submit(self, fn, *args, **kwargs):
        future = futures.Future()
        try:
            result = fn(*args, **kwargs)
        except BaseException:
            e = sys.exc_info()[1]
            future.set_exception(e)
        else:
            future.set_result(result)
        return future


class GeventPoolExecutor(futures.Executor):
    """ Wrapper for `gevent.pool.Pool`
    """

    def __init__(self, max_workers):
        import gevent.pool
        self.max_workers = max_workers
        self._pool = gevent.pool.Pool(max_workers)

    def submit(self, fn, *args, **kwargs):
        greenlet = self._pool.spawn(fn, *args, **kwargs)
        return GeventFuture(greenlet)

    def shutdown(self, wait=True):
        self._pool.kill(block=wait)


class GeventFuture(futures.Future):
    """ Wrapper for `Greenlet`
    """
    def __init__(self, greenlet):
        super(GeventFuture, self).__init__()
        #self._greenlet = gevent.Greenlet()
        self._greenlet = greenlet

    def result(self, timeout=None):
        import gevent
        try:
            return self._greenlet.get(timeout=timeout)
        except gevent.Timeout as e:
            raise futures.TimeoutError(e)

    def exception(self, timeout=None):
        # todo timeout
        return self._greenlet.exception

    def running(self):
        return not self.done()

    def done(self):
        return self._greenlet.ready()


__EXECUTOR_MAP = dict(thread=futures.ThreadPoolExecutor,
                      process=futures.ProcessPoolExecutor,
                      gevent=GeventPoolExecutor,
                      serial=SerialExecutor)

__EXECUTOR = None
def Executor():
    global __EXECUTOR
    if __EXECUTOR is None:
        from qarbon import config
        klass = __EXECUTOR_MAP[config.EXECUTOR.lower()] 
        __EXECUTOR = klass(config.MAX_WORKERS)
    return __EXECUTOR


def submit(fn, *args, **kwargs):
    return Executor().submit(fn, *args, **kwargs)
submit.__doc__ = futures.Executor.submit.__doc__

task = submit

def wait(fs, timeout=None, return_when=futures.ALL_COMPLETED):
    return futures.wait(fs, timeout=timeout, return_when=return_when)
wait.__doc__ = futures.wait.__doc__

def map(fn, *iterables, **kwargs):
    return Executor().map(fn, *iterables, **kwargs)
map.__doc__ = futures.Executor.map.__doc__

def shutdown(wait=True):
    global __EXECUTOR
    if __EXECUTOR is None:
        return
    result = __EXECUTOR.shutdown(wait=wait)
    __EXECUTOR = None
    return result
shutdown.__doc__ = futures.Executor.shutdown.__doc__


