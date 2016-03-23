# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.conf.urls import url

from .views import HealthCheckView


urlpatterns = [
    url(r'^healthcheck/$', HealthCheckView.as_view(), name='healthcheck'),
]
