# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import pytest

from requests import Timeout, ConnectionError, HTTPError

from panopticon.compat import mock
from panopticon.health import check_url


@pytest.mark.parametrize('url', ['', None])
def test_check_url_for_empty_url(url):
    result = check_url(url)
    assert result['healthy'] is False
    assert result['status_message'] == 'No URL specified to check.'


@pytest.mark.parametrize('exception', [Timeout, ConnectionError, HTTPError])
def test_check_url_connection_errors(exception):
    with mock.patch('panopticon.health.requests.get') as get_mock:
        get_mock.side_effect = exception

        result = check_url('https://dominatethe.world/api/v1/plans/')

        assert result['healthy'] is False
        assert result['status_message'].startswith('Error connecting to URL')


def test_check_url_with_unexpected_status_code():
    with mock.patch('panopticon.health.requests.get') as get_mock:
        get_mock.return_value = mock.Mock(status_code=300)

        result = check_url('https://dominatethe.world/api/v1/plans/')

        assert result['healthy'] is False
        assert result['status_message'].startswith(
            'server responded with unexpected status code: 300')


def test_check_url_for_available_url():
    with mock.patch('panopticon.health.requests.get') as get_mock:
        get_mock.return_value = mock.Mock(status_code=200)

        result = check_url('https://dominatethe.world/api/v1/plans/')

        assert result['healthy'] is True
        assert result['status_message'] == 'URL is available'
