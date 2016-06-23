# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import time
import atexit
import datadog

from functools import wraps

from .compat import mock
from . import PanopticonSettings


class DataDog(object):
    """
    Abstraction over the DataDog python client.

    Key methods are 'gauge', 'increment', 'decrement',
    'histogram', and 'timing'. These can all be called
    on the `DataDog` class to send metrics to DataDog.

    We recommend that metric names should generally follow a
    dot-hierarchy. For example, in a service called 'awesome', there might
    be metrics called 'awesome.web_requests' or 'awesome.worker.tasks'.
    Using a hierarchy makes it simpler to combine metrics from several
    services in a single DataDog dashboard.

    If the 'DATADOG_STATS_PREFIX' environment variable is defined, then
    its value will be prepended to all metric names, followed by a '.'.

    From the DataDog website:
        There are a few rules to stick to when naming metrics:
        * Metric names must start with a letter
        * Can only contain ascii alphanumerics, underscore and periods
          (other characters will get converted to underscores)
        * Should not exceed 200 characters (though less than 100 is generally
          preferred from a UI perspective)
        * Unicode is not supported
        * We recommend avoiding spaces

    Metric values may be integers or floating point values.

    Along with a metric value, DataDog accepts an arbitrary set of
    key:value *tags*. The keys should be strings, the values should
    generally also be strings. You can use tag values to split and combine
    metrics when generating graphs or alerts in DataDog. The DataDog
    python API accepts tags as lists of 'key:value' strings, and this
    API will also accept them as dicts.

    The 'event' method sends events to DataDog. Event names can be any
    string, but we also recommend using a dot-hierarchy for them.

    See http://docs.datadoghq.com/guides/metrics/ for more information
    about how DataDog collects different types of metrics.

    """
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
    def configure_settings(cls, settings):
        """
        Configure the settings to be used within datadog.
        """
        cls.STATS_ENABLED = cls._get_value_for_key(settings,
                                                   cls.KEY_DATADOG_ENABLED,
                                                   default=False)
        cls.STATS_PREFIX = cls._get_value_for_key(settings,
                                                  cls.KEY_DATADOG_STATS_PREFIX,
                                                  default=cls.STATS_PREFIX)

        api_key = cls._get_value_for_key(settings, cls.KEY_DATADOG_API_KEY)
        cls.settings[cls.KEY_DATADOG_API_KEY] = api_key

    @classmethod
    def stats(cls):
        """
        Get the threaded datadog client (singleton): `datadog.ThreadStats`.

        This will return a `mock.Mock` instance if the `DATADOG_ENABLED` setting
        is `False`. This makes it possible to run this in development without
        having to make any additional changes or conditional checks.

        :return datadog.ThreadState
        """
        if cls._stats_instance:
            return cls._stats_instance

        # If datadog is disabled by the Django setting DATADOG_ENABLED, we use
        # a mock object instead of the actual datadog client. This makes it
        # easier to switch it out without too much additional work and should
        # be good enough for development.
        api_key = cls.settings.get(cls.KEY_DATADOG_API_KEY, None)
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
        Get the metric name prefixed with the name in `DATADOG_STATS_PREFIX`,
        given a list of metric name components as args, or a single metric
        name.
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

    @classmethod
    def _convert_tags(cls, tags):
        """
        Convert tags, which may be a dict or iterable, into
        the DataDog format of a list of 'key:value' strings.

        To make it easier to write test assertions that validate
        mock calls, the resulting list is sorted.

        Args:
            tags (Dict, Sequence):

        Returns:
            [str]
        """
        if isinstance(tags, dict):
            result = [
                '{}:{}'.format(key, value)
                for key, value in tags.items()
            ]
        else:
            result = list(tags)

        return sorted(result)

    @classmethod
    def gauge(cls, metric_name, value, tags=None, **kwargs):
        """
        Record a gauge value (for a gauge, the latest value within any one
        minute is the value stored).

        Args:
            metric_name (str): name of the metric to be stored
            value (int or float): the value of the metric
            tags (list or dict): miscellaneous tags to describe the value
        """
        cls.stats().gauge(
            cls.get_metric_name(metric_name),
            value=value,
            tags=cls._convert_tags(tags),
            **kwargs
        )

    @classmethod
    def increment(cls, metric_name, value=1, tags=None, **kwargs):
        """
        Increment a metric_name value (all the increments and decrements within
        a given minute are summed together).

        Args:
            metric_name (str): name of the metric to be incremented
            value (int or float): how much to increment the metric value
            tags (list or dict): miscellaneous tags to describe the value
        """
        cls.stats().increment(
            cls.get_metric_name(metric_name),
            value=value,
            tags=cls._convert_tags(tags),
            **kwargs
        )

    @classmethod
    def decrement(cls, metric_name, value=1, tags=None, **kwargs):
        """
        Decrement a metric_name value (all the increments and decrements within
        a given minute are summed together).

        Args:
            metric_name (str): name of the metric to be decremented
            value (int or float): how much to decrement the metric value
            tags (list or dict): miscellaneous tags to describe the value
        """
        cls.stats().decrement(
            cls.get_metric_name(metric_name),
            value=value,
            tags=cls._convert_tags(tags),
            **kwargs
        )

    @classmethod
    def histogram(cls, metric_name, value, tags=None, **kwargs):
        """
        Send a histogram metric value. Histograms describe the distribution
        of the recorded values of a metric (minimum, maximum, average, count
        and the 75th, 85th, 95th and 99th percentiles).

        Args:
            metric_name (str): name of the metric to be stored
            value (int or float): the value of the metric
            tags (list or dict): miscellaneous tags to describe the value
        """
        cls.stats().histogram(
            cls.get_metric_name(metric_name),
            value=value,
            tags=cls._convert_tags(tags),
            **kwargs
        )

    @classmethod
    def event(cls, title, text, tags=None, **kwargs):
        """
        Record a timing metric.

        Note that an event title is not a metric name, so no
        DATADOG_STATS_PREFIX value is prepended to it.

        Args:
            title (str): Event title
            text (str or None): Optional event text (string), supports
                MarkDown (see http://docs.datadoghq.com/guides/markdown/ )
            tags (list or dict): miscellaneous tags to describe the value
        """
        cls.stats().event(
            title,
            text,
            tags=cls._convert_tags(tags),
            **kwargs
        )

atexit.register(DataDog.stop)
