# -*- coding: utf-8 -*-
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

requires = ['six', 'requests', 'datadog']
tests_requires = ['pytest', 'pytest-cache', 'pytest-cov', 'mock']


# Mock is part of Python 3 so we only need it in Python 2.x
if sys.version_info < (3,):
    tests_requires.append('mock')


dev_requires = ['tox', 'bumpversion', 'twine', 'wheel']


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='python-panopticon',
    version='0.2.2',
    description='A collection of healthcheck and monitoring helpers.',
    long_description='\n\n'.join([open('README.rst').read()]),
    license=open('LICENSE').read(),
    author='Mobify Research & Develpment Inc.',
    author_email='ops@mobify.com',
    url='https://python-panopticon.readthedocs.org',
    packages=['panopticon',
              'panopticon.django'],
    install_requires=requires,
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython'],
    extras_require={'test': tests_requires,
                    'dev': dev_requires},
    cmdclass={'test': PyTest})
