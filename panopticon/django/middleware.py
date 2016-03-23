# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import time

from panopticon.datadog import DataDog


class DataDogMiddleware(object):
    """
    Adapted from the middleware in this django app:

    https://github.com/conorbranagan/django-datadog
    """
    DD_REQUEST_START_ATTRIBUTE = '_dd_request_start'

    DD_REQUESTS_TIME = 'requests.time_ms'
    DD_REQUESTS_FAILED = 'requests.failed'
    DD_REQUESTS_SUCCESSFUL = 'requests.successful'

    def __init__(self):
        self.stats = DataDog.stats()

    def process_request(self, request):
        setattr(request, self.DD_REQUEST_START_ATTRIBUTE, time.time())

    def process_response(self, request, response):
        if not hasattr(request, self.DD_REQUEST_START_ATTRIBUTE):
            return response

        start_time = getattr(request, self.DD_REQUEST_START_ATTRIBUTE)
        request_time = time.time() - start_time

        self.stats.histogram(DataDog.get_metric_name(self.DD_REQUESTS_TIME),
                             int(request_time * 1000),  # report in milliseconds
                             tags=self._get_metric_tags(request))

        metric_name = DataDog.get_metric_name(self.DD_REQUESTS_SUCCESSFUL)
        self.stats.increment(metric_name,
                             tags=self._get_metric_tags(request))

        return response

    def process_exception(self, request, exception):
        title = 'Exception occured at {}'.format(request.path)

        self.stats.event(title=title,
                         text=str(exception),
                         aggregation_key=request.path,
                         alert_type='error')

        self.stats.increment(DataDog.get_metric_name(self.DD_REQUESTS_FAILED),
                             tags=self._get_metric_tags(request))

    def _get_metric_tags(self, request):
        return ['path:{}'.format(request.path)]
