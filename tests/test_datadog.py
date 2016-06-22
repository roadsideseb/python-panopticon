# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import collections

from panopticon.compat import mock

from panopticon.datadog import DataDog


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


def test_metrics():
    metric_prefix = test_metrics.__name__
    DataDog.configure_settings({'DATADOG_STATS_ENABLED': True,
                                'DATADOG_STATS_PREFIX': metric_prefix})

    mock_dd = DataDog.stats()
    for method in ['gauge', 'increment', 'decrement', 'histogram', 'event']:
        setattr(mock_dd, method, mock.Mock())

    DataDog.gauge('abc', 2, tags={'xyz1': 123})
    mock_dd.gauge.assert_called_with(
        metric_prefix + '.abc',
        value=2,
        tags=['xyz1:123']
    )

    DataDog.increment('def.fed', 3, tags={'xyz2': 456})
    mock_dd.increment.assert_called_with(
        metric_prefix + '.def.fed',
        value=3,
        tags=['xyz2:456']
    )

    DataDog.decrement('', 4, tags={'xyz3': 'ping'})
    mock_dd.decrement.assert_called_with(
        metric_prefix + '.',
        value=4,
        tags=['xyz3:ping']
    )

    DataDog.histogram('jkl', 1.23, tags={'xyz4': 4.56})
    mock_dd.histogram.assert_called_with(
        metric_prefix + '.jkl',
        value=1.23,
        tags=['xyz4:4.56']
    )

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
