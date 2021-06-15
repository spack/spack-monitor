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

The only dependency you should need for these examples is to install requests, which
we use here because it's easier than urllib (in spack we don't want to add a dependency
so we stick to urllib). You can use the requirements.txt in
the examples folder to do this.

.. code-block:: console

    $ pip install -r script/api-examples/requirements.txt


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
     'auth_instructions_url': 'https://spack-monitor.readthedocs.io/en/latest/getting_started/auth.html'}

 
Note that we provide this example script `service_info.py <https://github.com/spack/spack-monitor/blob/main/script/api-examples/service_info.py>`_ in the repository so you should be able to just run it to produce the example above:


.. code-block:: console

    $ python script/api-examples/service_info.py 


Also take notice that we are running these scripts *outside of the container* as you'd
imagine would be done with a service.


---------------------
Upload Config Example
---------------------

While most interactions with the API are going to come from spack, we do
provide an equivalent example and endpoint to upload a spec file, verbatim.
For this interaction, since we are modifying the database, you are required to export
your token and username first:

.. code-block:: console

    $ export SPACKMON_TOKEN=50445263afd8f67e59bd79bff597836ee6c05438
    $ export SPACKMON_USER=vsoch

    
For this example `upload_config.py <https://github.com/spack/spack-monitor/blob/main/script/api-examples/upload_config.py>`_
in the repository you'll see that by way of the `spackmon client <https://github.com/spack/spack-monitor/blob/main/script/spackmoncli.py>`_ 
we find this token in the environment, and add it as a base64 encoded authorization header.


.. code-block:: console

    $ python script/api-examples/upload_config.py specs/singularity-3.6.4.json $(spack --version)


If you run this inside the container, you can grab the version of spack from the host and
use directly as a string:


.. code-block:: console

    $ echo $(spack --version)
    $ python script/api-examples/upload_config.py specs/singularity-3.6.4.json 0.16.0-1379-7a5351d495


If you haven't added it yet (the full hash of the first package in the file is the unique id) you'll
see that it was added:

.. code-block:: console

    $ python script/api-examples/upload_config.py specs/singularity-3.6.4.json 
    The package was successfully created.
    {
        "message": "success",
        "data": {
            "full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
            "name": "singularity",
            "version": "3.6.4",
            "spack_version": "0.16.0-1379-7a5351d495",
            "specs": {
                "cryptsetup": "tmi4pf6umhalop7mi6zyiv7xjpalyzgb",
                "go": "dehg3ddu6gacrmnoexbxhjv2i2d76yq6",
                "libgpg-error": "4cvsg42wxksiup6x74mlabu6un55wjzc",
                "libseccomp": "kfx6zyjxzudw77e3xk6i73bcgi2cavgh",
                "pkgconf": "al2hlnux3cchfhwiv2sbejnxvnogibac",
                "shadow": "aozeq6ybtsnrs5phtonutwes7fe6yhcy",
                "squashfs": "vpemhhpzqqf7mvpzdvcg6szfah6mwt2q",
                "util-linux-uuid": "g362jjpzlfp3qhfm7gdery6v3xgeh3lg"
            }
        }
    }


That's a hint of the metadata that can be returned to a calling client.
In the context of spack, we actually don't need to pass around this metadata,
because spack always carries a representation of a package's full hash
and dependencies. If you've already added the package, you'll see:

.. code-block:: console

    $ python script/api-examples/upload_config.py specs/singularity-3.6.4.json $(spack --version)
    This package already exists in the database.


-------------------------
Local Save Upload Example
-------------------------

When you run spack install and ask the monitor to save local:

.. code-block:: console

   $ spack install --monitor --monitor-save-local singularity


This will generate a dated output directory in ``~/.spack/reports/monitor`` that
you might want to upload later. You'll again want to export your credentials:

.. code-block:: console

    $ export SPACKMON_TOKEN=50445263afd8f67e59bd79bff597836ee6c05438
    $ export SPACKMON_USER=vsoch

    
For this example `upload_save_local.py <https://github.com/spack/spack-monitor/blob/main/script/api-examples/upload_save_local.py>`_
in the repository you'll see that by way of the `spackmon client <https://github.com/spack/spack-monitor/blob/main/script/spackmoncli.py>`_  we can do this upload.

.. code-block:: console

    $ python script/api-examples/upload_save_local.py ~/.spack/reports/monitor/2021-06-14-17-02-27-1623711747/

In the above we run the script and provide the path to the directory we want to
upload results for. The script will upload spec objects, then retrieve the build id,
and finish up with phase logs and build statuses.





