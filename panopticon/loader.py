# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import structlog
import importlib

log = structlog.get_logger('panopticon.loader')


def load_healthcheck_modules(package_names, module_name='healthchecks'):
    for name in package_names:
        healthcheck_module = '{name}.{module}'.format(name=name,
                                                      module=module_name)

        try:
            importlib.import_module(healthcheck_module)
        except ImportError:
            log.debug('importing {} failed'.format(healthcheck_module))
        else:
            log.info('imported: {}'.format(healthcheck_module))
