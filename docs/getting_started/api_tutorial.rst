.. _getting-started_api_tutorial:

============
API Tutorial
============

In the scripts folder in the repository, you'll find a file ``spackmoncli.py``
that provides an example client for interacting with a Spack Monitor database.
The ``api-examples`` folder also includes these examples in script form.
Before doing this tutorial, you should have already started containers (:ref:`getting-started_install`),
and created a username and token (:ref:`getting-started_api`).

--------------------
Service Info Example
--------------------

Let's first create a client, and use it to get service info for the running server.
This section will also show us how to create a client, which we will do across
all examples here. This particular request does not require a token.

.. code-block:: python

    from spackmoncli import SpackMonitorClient


If we are using the server running on localhost, and the default endpoint, we don't
need to customize the arguments.

.. code-block:: python

    client = SpackMonitorClient()
    <spackmoncli.SpackMonitorClient at 0x7f24545fdb80>
    

However you could easily customize them as follows:


.. code-block:: python

    client = SpackMonitorClient(host="https://servername.org", prefix="ms2")
    <spackmoncli.SpackMonitorClient at 0x7f24545fdb80>


Next, let's ping the service info endpoint.

.. code-block:: python

    client.service_info()
     {'id': 'spackmon',
     'status': 'running',
     'name': 'Spack Monitor (Spackmon)',
     'description': 'This service provides a database to monitor spack builds.',
     'organization': {'name': 'spack', 'url': 'https://github.com/spack'},
     'contactUrl': 'https://github.com/spack/spack-monitor/issues',
     'documentationUrl': 'https://spack-monitor.readthedocs.io',
     'createdAt': '2021-02-10T10:40:19Z',
     'updatedAt': '2021-02-11T00:06:06Z',
     'environment': 'test',
     'version': '0.0.1',
     'auth_instructions_url': ''}

 
*I am still being written!*
