python-panopticon
#################


.. image:: https://travis-ci.org/mobify/python-panopticon.svg?branch=master
   :target: https://travis-ci.org/mobify/python-panopticon

Panopticon is a collection of health check and monitoring helpers that we use
at `Mobify <https://mobify.com>`_ for our services.


Installation
------------

The easiest way to install it is from PyPI::

    $ pip install python-panopticon


You can also install it straight from the repo:: 

    $ pip install https://github.com/mobify/python-panopticon/archive/master.zip


Setup with Django
-----------------

panopticon comes with a Django integration app that simplifies the setup. Make
sure you have the ``python-panopticon`` package installed.

Add the ``panopticon.django`` app into you ``INSTALLED_APPS`` settings and
configure the API key for Datadog by specifying ``DATADOG_API_KEY`` in your
settings. You are all done!

If you want your healthcheck to be automatically exposed on ``/healthcheck/`` you
can simply add the following line to your main project ``urls.py``:

.. code:: python

    #urls.py
    urlpatterns = [
        ...

        url(r'', include('panopticon.urls', namespace='panopticon')),
    ]

Using this view at this point requires ``django-rest-framework`` (DRF) to be
installed as a dependency. We'll probably changes it in the future but for now,
we are using DRF in our projects and it provides some additional features.

If you don't hook up ``panopticon.urls``, you can simply build your own view and
ignore this dependency.


Available Settings
------------------

* ``DATADOG_STATS_ENABLED`` : Enables or disables the Datadog wrapper in
  panopticon. If you disable panopticon, it'll use a ``mock.Mock`` object as
  the stats client. It is disabled by default.
* ``DATADOG_STATS_PREFIX`` : The prefix used for **all** Datadog metrics when
  submitted to the Datadog API. The default is ``panopticon``.


Adding a custom healthcheck in Django
-------------------------------------

If you are using the Django app to integrate it with Django, adding new health
checks is easy. Every application in ``INSTALLED_APPS`` will be checked for a 
``healthchecks.py`` module on startup. Loading each of these modules will
automatically register all health checks in that module. This is similar to how
``models.py`` and ``tasks.py`` (Celery) work.

Let's assume we have a ``monitoring`` Django app that should contain some simple
health checks. The first thing to do is creating a ``healthchecks.py`` file.
Within this file, we can now create a simple function that test the database
connection. All we have to do to hook it up is register it as a health check
and provide details about its success:

.. code:: python 

    from django.db import connection, DatabaseError

    @HealthCheck.register_healthcheck
    def database(data):
        cursor = connection.cursor()

        healthy = True
        status = 'database is available.'

        try:
            cursor.execute('SELECT 1;')
        except DatabaseError as exc:
            status = 'error connecting to the database: {}'.format(str(exc))
        finally:
            cursor.close()

        data[HealthCheck.HEALTHY] = healthy
        data[HealthCheck.STATUS_MESSAGE] = status

        return data

The name of the function, i.e. ``database`` in this case, will be used as the
component name for the health check result as defined in the response format
below.


The Response Format
-------------------

The health check format that we use makes sure that all health checks return an
agreed upon JSON response. This ensure that certain properties are always
present and can be relied upon for external processing, e.g. ``service_healthy``,
``timestamp``, ``components`` and ``healthy`` within each of the components.

.. code:: javascript

    {
        // This represents the overall health of the service
        // If all of the components are healthy this should be true, false otherwise.
        "service_healthy": true,
     
        // The instant when the response was generated. This is useful to determine
        // if the health check response is up to date or stale, for example because it
        // was cached. This is in ISO8601 format.
        "timestamp": "2014-09-03T23:09:38.702Z",
     
        // We also expose the health status for each internal component
        // of the service. Besides a “healthy” flag this can also include
        // metadata like the number of queued jobs or average processing times.
        // We expose this information in a list so that monitoring tools can parse
        // and visualize this information easily.
        "components": {
            "database": {
                "healthy":  true,
                "response_time": 0.00123,
                "friendly_status": "The database is working awesomely great!"
            },
            "background_jobs": {
                "healthy":  true,
                "response_time": 0.00123,
                "queued_jobs": 423
            }
        }
    }


Setup Development
-----------------

The development setup is using `tox <https://tox.readthedocs.io/en/latest>`_
for testing against various versions of Python. Running tox tests is quit
simple for a given Python version that you have installed locally. For instance
running tox with Python 2.7.10::

    $ pip install tox
    $ tox -e py27

or for Python 3.5::

    $ tox -e py35


If you prefer to install and run the tests inside a virtualenv, you can install
all the test and release requirements inside a virtualenv using::

    $ pip install -e ".[test]"
    $ pip install -e ".[dev]"


Creating a Release
------------------

Creating a new release is simple. We use `bumpversion
<https://github.com/peritus/bumpversion>`_ which ensures that naming tags and
updating *all* version numbers in the Python code is ensured. To create a new
version specify the type of version bump (either *major*, *minor* or *patch*)
and bumpversion will do the rest. For a patch it looks like this::

    $ bumpversion patch

This will do the following:

* Change all version strings defined in ``bumpversion.cfg``.
* Create a new commit.
* Create a new tag with the given version number.
   
**Note** A new release should only be created on the ``master`` branch after
one or more changes have been merged and tested.

After releasing a new version, the commit and tag have to be pushed to github::

    $ git push 
    $ git push --tags

You can now release this version to PyPI using the Makefile. This requires
the password for the ``mobify`` user to be exported in your shell. You can find
it in LastPass::

    $ PYPI_PASSWORD=<the password> make release


License
-------

This code is licensed under the `MIT License`_.

.. _`MIT License`: https://github.com/mobify/python-panopticon/blob/master/LICENSE
