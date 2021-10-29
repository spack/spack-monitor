.. _development-analysis:

====================
Analysis Development
=====================

This short guide is me taking notes to prepare for an analysis that can look across
versions and compilers. For my first test I want to install zlib across
several versions of a package and compilers. Note that this requires
`this branch <https://github.com/vsoch/spack/pull/new/vsoch/db>`_.

Setup 
-----

Before doing this, you should have exported a spack monitor token and username
in your envrionment.

.. code-block:: console

    SPACKMON_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
    SPACKMON_USER=vsoch


We also need to ensure that everything builds with debug.

.. code-block:: console

    $ . /share/spack/setup-env.sh
    export SPACK_ADD_DEBUG_FLAGS=true


Test
----

And then here is how to install zlib with using spack monitor (locally) and then
running the analyzer for the same set:


.. code-block:: console

    # Install ALL versions of zlib with default compiler
    $ spack  install --monitor --all --monitor-tag smeagle zlib

    # Analyze all versions of zlib plus recursive dependents
    $ spack analyze --monitor run --analyzer smeagle --recursive --all zlib


I did a sanity check to see the results in the database:

.. code-block:: console

    $ docker exec -it uwsgi bash
    p(sm) root@8a3433dedba8:/code# python manage.py shell
    Python 3.8.12 | packaged by conda-forge | (default, Oct 12 2021, 21:59:51) 
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.28.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: from spackmon.apps.main.models import Attribute
    
    In [2]: Attribute.objects.all()
    Out[2]: <QuerySet [<Attribute: Attribute object (1)>, <Attribute: Attribute object (2)>]>

    In [3]: Attribute.objects.first()
    Out[3]: <Attribute: Attribute object (1)>

    In [4]: Attribute.objects.first().json_value
    Out[4]: 
    {'library': '/data/libz.so.1.2.11',
     'locations': [{'function': {'name': 'free',
        'type': 'Function',
        'direction': 'import'}},
      {'function': {'name': '__errno_location',
        'type': 'Function',
        'direction': 'import'}},
      {'function': {'name': 'write', 'type': 'Function', 'direction': 'import'}},
      {'function': {'name': 'strlen', 'type': 'Function', 'direction': 'import'}},

Yes!

Change Compiler
---------------

And now we want to install the same versions of zlib with different compilers.

.. code-block:: console

    # Install ALL versions of zlib
    $ spack  install --monitor --all --monitor-tag smeagle zlib %gcc@8.4.0
    $ spack  install --monitor --all --monitor-tag smeagle zlib %gcc@7.5.0

    # Analyze all versions of zlib plus recursive dependents
    $ spack analyze --monitor run --analyzer smeagle --recursive --all zlib%gcc@8.4.0
    $ spack analyze --monitor run --analyzer smeagle --recursive --all zlib%gcc@7.5.0

