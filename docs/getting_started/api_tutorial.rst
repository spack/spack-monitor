.. _getting-started_api_tutorial:

============
API Tutorial
============

For this tutorial, you should have already started containers (:ref:`getting-started_install`)
and created your user account and token (:ref:`getting-started_authentication`).

API Examples
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

 
Note that we provide this example script `in the repository <https://github.com/spack/spack-monitor/blob/main/script/api-examples/service_info.py>`_ so you should be able to just run it to produce the example above:

.. code-block:: python

    $ python script/api-examples/service_info.py 


Also take notice that we are running these scripts *outside of the container* as you'd
imagine would be done with a service.


-------------------
Upload Spec Example
-------------------

While most interactions with the API are going to come from spack, we do
provide an equivalent example and endpoint to upload a spec file, verbatim.
For this interaction, since we are modifying the database, you are required to export
your token and username first:

.. code-block:: console

    $ export SPACKMON_TOKEN=50445263afd8f67e59bd79bff597836ee6c05438
    $ export SPACKMON_USER=vsoch

For this example `in the repository <https://github.com/spack/spack-monitor/blob/main/script/api-examples/upload_spec.py>`_
you'll see that by way of the `spackmon client <https://github.com/spack/spack-monitor/blob/main/script/spackmoncli.py>`_ 
we find this token in the environment, and add it as a base64 encoded authorization header.


.. code-black:: console

    $ python script/api-examples/upload_spec.py specs/singularity-3.6.4.json 


If you haven't added it yet (the full hash of the first spec is the unique id) you'll
see that it was added:

.. code-block:: console

    $ python script/api-examples/upload_spec.py specs/singularity-3.6.4.json 
    The configuration was successfully created.

If you've already added it, you'll see:

.. code-block:: console

    $ python script/api-examples/upload_spec.py specs/singularity-3.6.4.json 
    This configuration already exists in the database.


