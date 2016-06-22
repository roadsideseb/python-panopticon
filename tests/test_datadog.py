# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import collections
import random
import string

from panopticon.compat import mock
from panopticon.datadog import DataDog
import pytest


def random_string(
    choose_from=None,
    length=8
):
    """
    Return a random sequence of characters

    Args:
        choose_from (Sequence): he set of eligible characters - by default
            the set is string.ascii_lowercase + string.digits
        length (int): the length of the sequence to be
            returned (in characters, default 8)
    Returns (string)
    """
    choices = list(choose_from or (string.ascii_lowercase + string.digits))
    return ''.join(
        random.choice(choices)
        for _ in range(length)
    )


def test_can_create_prefixed_metric_name():
    DataDog.configure_settings({'DATADOG_STATS_ENABLED': True,
                               'DATADOG_STATS_PREFIX': 'my_fancy_prefix'})

    DataDog.stats()

    assert DataDog.STATS_ENABLED is True
    assert DataDog.STATS_PREFIX == 'my_fancy_prefix'

    assert DataDog.get_metric_name('fancy_pants.metric') == 'my_fancy_prefix.fancy_pants.metric'  # noqa


def test_track_time():
    DataDog.configure_settings({'DATADOG_STATS_PREFIX': 'my_fancy_prefix'})

    with mock.patch('panopticon.datadog.time.time') as time:
        time.side_effect = [1, 2]
        DataDog.stats().histogram = mock.Mock()

        @DataDog.track_time('track_time_test')
        def test_function():
            pass

        test_function()

        histogram = DataDog.stats().histogram

        assert histogram.call_count == 1
        assert histogram.call_args[0] == ('my_fancy_prefix.track_time_test', 1)


def test_api_key():
    DataDog.configure_settings({'DATADOG_API_KEY': 'test_api_key'})

    configured_api_key = DataDog.settings[DataDog.KEY_DATADOG_API_KEY]

    assert configured_api_key == 'test_api_key'


@pytest.mark.parametrize(
    'method_name',
    ['gauge', 'increment', 'decrement', 'histogram']
)
def test_metrics(method_name):
    metric_prefix = test_metrics.__name__
    DataDog.configure_settings({'DATADOG_STATS_ENABLED': True,
                                'DATADOG_STATS_PREFIX': metric_prefix})

    mock_dd = DataDog.stats()
    mock_dd.reset_mock()
    mocked_method = mock.Mock()
    setattr(mock_dd, method_name, mocked_method)

    dd_method = getattr(DataDog, method_name)
    metric_name = random_string()
    value = random.randint(1, 11)

    tags = collections.OrderedDict(
        (
            (random_string(), random_string())
            for _ in range(random.randint(1, 4))
        )
    )

    dd_method(metric_name, value, tags=tags)

    mocked_method.assert_called_once()
    mocked_method.assert_called_with(
        metric_prefix + '.' + metric_name,
        value=value,
        tags=[
            key + ':' + value
            for key, value in tags.items()
        ]
    )


def test_event():
    metric_prefix = test_event.__name__
    DataDog.configure_settings({'DATADOG_STATS_ENABLED': True,
                                'DATADOG_STATS_PREFIX': metric_prefix})

    mock_dd = DataDog.stats()
    mock_dd.reset_mock()
    mock_dd.event = mock.Mock()

    tags = collections.OrderedDict(
        [
            ('xyz5', 567),
            ('abc2', 'pqr')
        ]
    )

    DataDog.event('mno', 'This is the text', tags=tags)
    mock_dd.event.assert_called_with(
        'mno',
        'This is the text',
        tags=['xyz5:567', 'abc2:pqr']
    )
