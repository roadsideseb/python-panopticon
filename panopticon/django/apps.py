# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.apps import apps, AppConfig


class PanopticonConfig(AppConfig):
    name = 'panopticon.django'
    label = 'panopticon'
    verbose_name = 'Panopticon'

    def ready(self):
        package_names = (a.module.__name__ for a in apps.get_app_configs())

        from panopticon.loader import load_healthcheck_modules
        load_healthcheck_modules(package_names)

        from django.conf import settings
        from panopticon.datadog import DataDog
        DataDog.configure_settings(settings)
