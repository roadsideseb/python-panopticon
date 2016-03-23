from panopticon.compat import mock

from panopticon.datadog import DataDog


def test_can_create_prefixed_metric_name():
    DataDog.configue_settings({'DATADOG_STATS_ENABLED': True,
                               'DATADOG_STATS_PREFIX': 'my_fancy_prefix'})

    DataDog.stats()

    assert DataDog.STATS_ENABLED is True
    assert DataDog.STATS_PREFIX == 'my_fancy_prefix'

    assert DataDog.get_metric_name('fancy_pants.metric') == 'my_fancy_prefix.fancy_pants.metric'  # noqa


def test_track_time():
    DataDog.configue_settings({'DATADOG_STATS_PREFIX': 'my_fancy_prefix'})

    with mock.patch('panopticon.datadog.time.time') as time:
        time.side_effect = [1, 2]
        histogram = DataDog.stats().histogram = mock.Mock()

        @DataDog.track_time('track_time_test')
        def test_function():
            pass

        test_function()

        histogram = DataDog.stats().histogram

        assert histogram.call_count == 1
        assert histogram.call_args[0] == ('my_fancy_prefix.track_time_test', 1)
