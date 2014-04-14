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

"""Engine."""

__all__ = ["Engine", "ReturnResult", "Runner", "return_result"]

import sys
import time
import types
import functools
from concurrent import futures


POOL_TIMEOUT = 0.02


class Task(object):
    """ Represents single async operation.

    Accepts callable and optionally its ``args`` and ``kwargs``::

        result = yield Task(time_consuming_operation, arg, some_kwarg=1)
    """

    #: Executor class (from `concurrent.futures`) overridden in subclasses
    #: default is `ThreadPoolExecutor`
    executor_class = futures.ThreadPoolExecutor
    #: Maximum number of workers, mainly used in MultiTask
    max_workers = 1

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return self.func(*self.args, **self.kwargs)

    __call__ = start

    def __repr__(self):
        return ('<%s(%s, %r, %r)>' %
                (self.__class__.__name__, self.func.__name__,
                 self.args, self.kwargs))


class ProcessTask(Task):
    """ Task executed in separate process pool
    """
    executor_class = futures.ProcessPoolExecutor


class MultiTask(Task):
    """ Tasks container, executes passed tasks simultaneously in ThreadPool
    """
    def __init__(self, tasks, max_workers=None, skip_errors=False,
                 unordered=False):
        """
        :param tasks: list/tuple/generator of tasks
        :param max_workers: number of simultaneous workers,
                            default is number of tasks
        :param skip_errors: if True, tasks which raised exceptions will not be
                            in resulting list/generator
        :param unordered: if True, result will be returned as  generator,
                            which yields task's results as it's ready.
        """
        self.tasks = list(tasks)
        self.max_workers = max_workers if max_workers else len(self.tasks)
        self.skip_errors = skip_errors
        self.unordered = unordered

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.tasks)

    def wait(self, executor, spawned_futures, timeout=None):
        """ Return True if all tasks done, False otherwise
        """
        return not futures.wait(spawned_futures, timeout).not_done


class MultiProcessTask(MultiTask):
    """ Tasks container, executes passed tasks simultaneously in ProcessPool
    """
    executor_class = futures.ProcessPoolExecutor

    def __init__(self, tasks, max_workers=None, skip_errors=False, **kwargs):
        """
        Same parameters as :class:`MultiTask` but one is different:

        :param max_workers: number of simultaneous workers,
                            default is number of CPU cores
        """
        if max_workers is None:
            import multiprocessing
            max_workers = multiprocessing.cpu_count()
        super(MultiProcessTask, self).__init__(
            tasks, max_workers, skip_errors, **kwargs
        )


# TODO docs about monkey_patch
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


# TODO more greenlet methods, also check not overridden Future methods
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


class GTask(Task):
    """ Task executed in `gevent` Pool
    """
    executor_class = GeventPoolExecutor


class MultiGTask(MultiTask):
    """ Multiple tasks executed in `gevent` Pool simultaneously
    """
    executor_class = GeventPoolExecutor

    def wait(self, executor, spawned_futures, timeout=None):
        executor._pool.join(timeout)
        return all(f.done() for f in spawned_futures)


class ReturnResult(Exception):
    """ Exception Used to return result from generator
    """
    def __init__(self, result):
        super(ReturnResult, self).__init__()
        self.result = result


class Engine(object):
    """ Engine base class

    After creating engine instance, set :attr:`main_app` property
    (not needed with PyQt/PySide)

    Decorate generator with :meth:`@async <async>` to execute tasks yielded
    from generator in separate executor and rest operations in GUI thread.

    Subclasses should implement :meth:`update_gui`.
    """
    def __init__(self, pool_timeout=POOL_TIMEOUT):
        """
        :param pool_timeout: time in seconds which GUI can spend in a loop
        """
        self.pool_timeout = pool_timeout
        #: main application instance
        self.main_app = None

    def async(self, func):
        """ Decorator for asynchronous generators.

        Any :class:`Task`, :class:`ProcessTask` or :class:`GTask` yielded from
        generator will be executed in separate thread, process or greenlet
        accordingly. For example gui application can has following button
        click handler::

            engine = PyQtEngine()
            ...
            @engine.async
            def on_button_click():
                # do something in GUI thread
                data = yield Task(do_time_consuming_work, param)
                update_gui_with(data)  # in main GUI thread

        If some task raises :class:`ReturnResult`, it's value will be returned
        .. seealso:: :func:`return_result`
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            if isinstance(gen, types.GeneratorType):
                return self.create_runner(gen).run()
        return wrapper

    def create_runner(self, gen):
        """ Creates :class:`Runner` instance

        :param gen: generator which returns async tasks

        Can be overridden if you want custom ``Runner``
        """
        return Runner(self, gen)

    def update_gui(self):
        """ Allows GUI to process events

        Should be overridden in subclass
        """
        time.sleep(self.pool_timeout)


class Runner(object):
    """ Internal class that runs tasks returned by generator
    """
    def __init__(self, engine, gen):
        """
        :param engine: :class:`Engine` instance
        :param gen: Generator which yields tasks
        """
        self.engine = engine
        self.gen = gen

    def run(self):
        """ Runs generator and executes tasks
        """
        gen = self.gen
        task = next(gen)  # start generator and receive first task
        while True:
            try:
                if isinstance(task, (list, tuple)):
                    assert len(task), "Empty tasks sequence"
                    first_task = task[0]
                    if isinstance(first_task, ProcessTask):
                        task = MultiProcessTask(task)
                    elif GTask and isinstance(first_task, GTask):
                        task = MultiGTask(task)
                    else:
                        task = MultiTask(task)

                with task.executor_class(task.max_workers) as executor:
                    if isinstance(task, MultiTask):
                        task = self._execute_multi_task(gen, executor, task)
                    else:
                        task = self._execute_single_task(gen, executor, task)
            except StopIteration:
                break
            except ReturnResult as e:
                gen.close()
                return e.result

    def _execute_single_task(self, gen, executor, task):
        future = executor.submit(task)
        while True:
            try:
                result = future.result(self.engine.pool_timeout)
            except futures.TimeoutError:
                self.engine.update_gui()
            # TODO canceled error
            except Exception:
                return gen.throw(*sys.exc_info())
            else:
                return gen.send(result)

    def _execute_multi_task(self, gen, executor, task):
        if task.unordered:
            results_gen = self._execute_multi_gen_task(gen, executor, task)
            return gen.send(results_gen)

        future_tasks = [executor.submit(t) for t in task.tasks]
        while True:
            if not task.wait(executor, future_tasks, self.engine.pool_timeout):
                self.engine.update_gui()
            else:
                break
        if task.skip_errors:
            results = []
            for f in future_tasks:
                try:
                    results.append(f.result())
                except Exception:
                    pass
        else:
            try:
                results = [f.result() for f in future_tasks]
            except Exception:
                return gen.throw(*sys.exc_info())
        return gen.send(results)

    def _execute_multi_gen_task(self, gen, executor, task):
        unfinished = set(executor.submit(t) for t in task.tasks)
        while unfinished:
            if not task.wait(executor, unfinished, self.engine.pool_timeout):
                self.engine.update_gui()
            done = set(f for f in unfinished if f.done())
            for f in done:
                try:
                    result = f.result()
                except Exception:
                    if not task.skip_errors:
                        raise
                else:
                    yield result
            unfinished.difference_update(done)


def return_result(result):
    """ Allows to return result from generator

    Internally it raises :class:`ReturnResult` exception, so take in mind, that
    it can be catched in catch-all block
    """
    raise ReturnResult(result)

