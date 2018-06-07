import httplib

import django
from django.conf import settings
from django.test import SimpleTestCase


settings.configure(DEBUG=True,
                   ROOT_URLCONF='urls',
                   # `auth` and `contenttypes` to stop `rest_framework` from blowing up.
                   INSTALLED_APPS=['django.contrib.auth',
                                   'django.contrib.contenttypes',
                                   'panopticon.django'],
                   MIDDLEWARE_CLASSES=[])

django.setup()


class TestHealthCheckView(SimpleTestCase):
    def test(self):
        response = self.client.get('/healthcheck/')
        self.assertEqual(response.status_code, httplib.OK)
