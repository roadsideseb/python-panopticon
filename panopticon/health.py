# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import time
import requests

from functools import wraps
from datetime import datetime
from collections import namedtuple

from .datadog import DataDog


HealthCheckResult = namedtuple('HealthCheckResult',
                               ('name', 'data', 'is_healthy'))


class HealthCheck(object):
    HEALTHY = 'healthy'
    RESPONSE_TIME = 'response_time'
    SERVICE_HEALTHY = 'service_healthy'
    TIMESTAMP = 'timestamp'
    COMPONENTS = 'components'
    STATUS_MESSAGE = 'status_message'

    health_checks = {}

    @classmethod
    def register_healthcheck(cls, func):
        func_name = func.__name__

        @wraps(func)
        def wrapped(*args, **kwargs):
            # Let's pass in a pre-populated dict so we can ensure certain
            # values being in the dict.
            data = {
                cls.HEALTHY: False,
                cls.STATUS_MESSAGE: "Health check didn't provide a status 😭."}

            start = time.time()

            # If we don't get a useful set of data back from the health check
            # we use the default dict from above to ensure consistency
            data = func(data, *args, **kwargs) or data

            # We only set the response time if it's not already been added
            # by the health check function itself.
            if cls.RESPONSE_TIME not in data:
                data[cls.RESPONSE_TIME] = time.time() - start

            # Let's trigger an event in Datadog if a healthcheck fails so we
            # can see how it effects other metrics.
            healthy = data.get(cls.HEALTHY, False)
            if not healthy:
                DataDog.stats().event(
                    title='Healthcheck {} failed'.format(func_name),
                    text=str(data),
                    tags=['application:healtcheck'],
                    alert_type='error')

            return HealthCheckResult(name=func_name,
                                     data=data,
                                     is_healthy=healthy)

        if func_name not in cls.health_checks:
            cls.health_checks[func_name] = wrapped

        return wrapped

    def get_health_check_functions(self):
        return self.health_checks.values()

    def run(self):
        components = []

        for health_check in self.get_health_check_functions():
            result = health_check()
            components.append(result)

        is_healthy = all(r.is_healthy for r in components)

        data = {self.SERVICE_HEALTHY: is_healthy,
                self.TIMESTAMP: datetime.now().isoformat(),
                self.COMPONENTS: {r.name: r.data for r in components}}

        return HealthCheckResult(name='system',
                                 data=data,
                                 is_healthy=is_healthy)


def check_url(url, expected_status=200, timeout=5):
    """
    A simple check if `url` is reachable and resturns `expected_status`.
    """
    if not url:
        return {HealthCheck.HEALTHY: False,
                HealthCheck.STATUS_MESSAGE: 'No URL specified to check.'}

    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        message = 'Error connecting to URL: {}'.format(str(exc))
        return {HealthCheck.HEALTHY: False,
                HealthCheck.STATUS_MESSAGE: message}

    if expected_status == response.status_code:
        return {HealthCheck.HEALTHY: True,
                HealthCheck.STATUS_MESSAGE: 'URL is available'}

    message = 'server responded with unexpected status code: {}'.format(
        response.status_code)

    return {HealthCheck.HEALTHY: False,
            HealthCheck.STATUS_MESSAGE: message}
