# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import time
import atexit
import datadog

from functools import wraps

from .compat import mock
from . import PanopticonSettings


class DataDog(object):
    KEY_DATADOG_API_KEY = 'DATADOG_API_KEY'
    KEY_DATADOG_ENABLED = 'DATADOG_STATS_ENABLED'
    KEY_DATADOG_STATS_PREFIX = 'DATADOG_STATS_PREFIX'

    # this is just the default
    STATS_ENABLED = False
    STATS_PREFIX = 'panopticon'

    ROLLUP_INTERVAL = 10
    FLUSH_INTERVAL = 10

    _stats_instance = None
    settings = PanopticonSettings()

    @staticmethod
    def _get_value_for_key(settings, key, default=None):
        try:
            value = settings.get(key, default)
        except AttributeError:
            value = getattr(settings, key, default)

        return value

    @classmethod
    def configue_settings(cls, settings):
        """
        Configure the settings to be used within datadog.
        """
        cls.STATS_ENABLED = cls._get_value_for_key(settings,
                                                   cls.KEY_DATADOG_ENABLED,
                                                   default=False)
        cls.STATS_PREFIX = cls._get_value_for_key(settings,
                                                  cls.KEY_DATADOG_STATS_PREFIX,
                                                  default=cls.STATS_PREFIX)

        api_key = cls._get_value_for_key(cls.settings, cls.KEY_DATADOG_API_KEY)
        setattr(cls.settings, cls.KEY_DATADOG_API_KEY, api_key)

    @classmethod
    def stats(cls):
        """
        Get the threaded datadog client (singleton): `datadog.ThreadStats`.

        This will return a `mock.Mock` instance if the `DATADOG_ENABLED` setting
        is `False`. This makes it possible to run this in development without
        having to make any additional changes or conditional checks.
        """
        if cls._stats_instance:
            return cls._stats_instance

        # If datadog is disabled by the Django setting DATADOG_ENABLED, we use
        # a mock object instead of the actual datadog client. This makes it
        # easier to switch it out without too much additional work and should
        # be good enough for development.
        api_key = getattr(cls.settings, cls.KEY_DATADOG_API_KEY, None)
        if cls.STATS_ENABLED is False or not api_key:
            cls._stats_instance = mock.Mock()

        else:
            datadog.initialize(api_key=api_key)

            cls._stats_instance = datadog.ThreadStats()
            cls._stats_instance.start(roll_up_interval=cls.ROLLUP_INTERVAL,
                                      flush_interval=cls.FLUSH_INTERVAL)

        return cls._stats_instance

    @classmethod
    def get_metric_name(cls, *args):
        """
        Get the metric name prefixed with the name in `DATADOG_STATS_PREFIX`.
        """
        return '.'.join((cls.STATS_PREFIX,) + args)

    @classmethod
    def stop(cls):
        """
        Ensure that we flush all metrics before shutting down the client.
        """
        if not cls._stats_instance:
            return

        cls._stats_instance.flush(time.time() + cls.ROLLUP_INTERVAL)

        try:
            cls._stats_instance.stop()
        except Exception:  # noqa
            pass

        cls._stats_instance = None

    @classmethod
    def track_time(cls, metric_name=None):
        """
        A decorator that tracks execution time for any wrapped function.

        The `metric_name` is optional and will default to the function name. In
        both cases, they full metric name will include the
        `DATADOG_STATS_PREFIX`.

        To apply this decorator to a class' method, use the Django utility
        decorator `method_decorator`::

            from django.utils.decorators import method_decorator
            from brain.monitoring.datadog import DataDog

            class SomeClass(object):

                @method_decorator(DataDog.track_time)
                def method_to_wrap(self, *args, **kwargs):
                    pass

        """

        def track_time_decorator(func):
            name = metric_name or func.__name__

            @wraps(func)
            def wrapped_func(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                request_time = time.time() - start

                metric_name = cls.get_metric_name(name)
                cls.stats().histogram(metric_name, request_time)

                return result

            return wrapped_func

        return track_time_decorator


atexit.register(DataDog.stop)
