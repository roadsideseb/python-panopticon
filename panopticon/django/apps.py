from django.apps import apps, AppConfig

from panopticon.loader import load_healthcheck_modules


class PanopticonConfig(AppConfig):
    name = 'panopticon.django'
    app_name = 'panopticon'
    verbose_name = 'Panopticon'

    def ready(self):
        package_names = (a.module.__name__ for a in apps.get_app_configs())
        load_healthcheck_modules(package_names)
