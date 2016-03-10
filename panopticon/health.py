import time

from functools import wraps
from datetime import datetime
from collections import namedtuple


HealthCheckResult = namedtuple('HealthCheckResult',
                               ('name', 'data', 'is_healthy'))


class HealthCheck(object):
    """
    A generic handler for health checks to register and run them.
    """
    HEALTY = 'healthy'
    RESPONSE_TIME = 'response_time'
    SERVICE_HEALTHY = 'service_healthy'
    TIMESTAMP = 'timestamp'
    COMPONENTS = 'components'
    STATUS_MESSAGE = 'status_message'

    health_checks = {}

    @classmethod
    def register_healthcheck(cls, func):
        """
        A decorator to register a health check function.

        A health check function is an arbitrary function that will accept a
        `data` dictionary as the first argument::

                @HealthCheck.register_healthcheck
                def my_health_check(data):
                    pass
        """
        func_name = func.__name__

        @wraps(func)
        def wrapped(*args, **kwargs):
            # Let's pass in a pre-populated dict so we can ensure certain
            # values being in the dict.
            data = {
                cls.HEALTY: False,
                cls.STATUS_MESSAGE: "Health check didn't provide a status 😭."}

            start = time.time()

            # If we don't get a useful set of data back from the health check
            # we use the default dict from above to ensure consistency
            data = func(data, *args, **kwargs) or data

            # We only set the response time if it's not already been added
            # by the health check function itself.
            if cls.RESPONSE_TIME not in data:
                data[cls.RESPONSE_TIME] = time.time() - start

            return HealthCheckResult(name=func_name,
                                     data=data,
                                     is_healthy=data.get(cls.HEALTY, False))

        if func_name not in cls.health_checks:
            cls.health_checks[func_name] = wrapped

        return wrapped

    def run(self):
        components = []

        for health_check in self.health_checks.values():
            result = health_check()
            components.append(result)

        is_healthy = all([r.is_healthy for r in components])

        data = {self.SERVICE_HEALTHY: is_healthy,
                self.TIMESTAMP: datetime.now().isoformat(),
                self.COMPONENTS: {r.name: r.data for r in components}}

        return HealthCheckResult(name='system',
                                 data=data,
                                 is_healthy=is_healthy)
