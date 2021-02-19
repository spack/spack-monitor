.. _getting-started_install:

======================
Bringing Up Containers
======================

Installation comes down to bringing up containers. You likely want to start with
your database in a container, and for a more substantial service, update
the database credentials to be for something more production oriented.
For using Spackmon you will need:

 - `Docker <https://docs.docker.com/get-docker/>`_
 - `docker-compose <https://docs.docker.com/compose/install/>`_


Once you have these dependencies, you'll first want clone the repository.

.. code-block:: console

     $ git clone git@github.com:spack/spack-monitor.git
     $ cd spack-monitor

Then you can build your container, which we might call `spack/spackmon`.
To do this with docker-compose:


.. code-block:: console

    $ docker-compose build
      
Note that if you just do ``docker-compose up -d`` without building, it will build
it for you. It's good practice to keep these steps separate so you can monitor them
more closely. Once you have the base container built, you can bring it up (which also will pull
the other containers for nginx and the database).


.. code-block:: console

    $ docker-compose up -d


You can verify they are running without any exit error codes:

.. code-block:: console

    $ docker-compose ps
            Name                       Command               State         Ports       
    -----------------------------------------------------------------------------------
    spack-monitor_db_1      docker-entrypoint.sh postgres    Up      5432/tcp          
    spack-monitor_nginx_1   /docker-entrypoint.sh ngin ...   Up      0.0.0.0:80->80/tcp
    spack-monitor_uwsgi_1   /bin/sh -c /code/run_uwsgi.sh    Up      3031/tcp  


And you can look at logs for the containers as follows:

.. code-block:: console

    $ docker-compose logs
    $ docker-compose logs uwsgi
    $ docker-compose logs db
    $ docker-compose logs nginx


Great! Now you are ready to start interacting with your Spack Monitor. Before we
do that, let's discuss the different ways that you can interact.    

Spackmon Interactions
=====================

There are two use cases that might be relevant to you:

 - you have existing configuration files that you want to import
 - you have a spack install that you want to build with, and directly interact
 
Import Existing Specs
*********************

For this case, we want to generate and then import a custom configuration. But to be 
clear, a configuration is simply a package with it's dependencies, meaning that the
unique id for it is the ``full_hash``. Let's make that first. As noted in the :ref:`development-background` 
section, there is a script provided that will make it easy to generate a spec,
and *note that we generate it with dependency (package) links using a full instead of a build hash*. 
Let's do that first. Since we need spack (on our host) we will run this outside of the container.
Make sure that you have exported the spack bin to your path:

.. code-block:: console

    $ export PATH=$PATH:/path/to/spack/bin


From the repository, generate a spec file. There is one provided for Singularity
if you want to skip this step. It was generated as follows:

.. code-block:: console

     $ mkdir -p specs
                                     # lib       # outdir
     $ ./script/generate_random_spec.py singularity specs
    ...
    wont include py-cython due to variant constraint +python
    Success! Saving to /home/vanessa/Desktop/Code/spack-monitor/specs/singularity-3.6.4.json


**Important** If you want to generate this on your own, you must use a full hash,
as this is what the database uses as a unique identifier for each package.

.. code-block:: console

    spack spec --json --hash-type full_hash singularity
    

Your containers should already be running. Before we shell into the container,
let's grab the spack version, which we will need for the request.

.. code-block:: console

    $ echo $(spack --version)
    $ 0.16.0-1379-7a5351d495

Let's now shell into the container, where we can interact directly with the database.

.. code-block:: console
   
   $ docker exec -it spack-monitor_uwsgi_1 bash


The script ``manage.py`` provides an easy interface to run custom commands. For example,
here is how to do migrations and setup the database (this is done automatically for
you when you first bring up the container in ``run_uwsgi.sh``, but if you need to change
models or otherwise update the application, you'll need to run these manually in the
container:

.. code-block:: console

    $ python manage.py makemigrations main
    $ python manage.py makemigrations users
    $ python manage.py migrate
    

When the database is setup (the above commands are run, by default)
we can run a command to do the import. Note that we are including the spec file
and the spack version (so you should have it on your path):

.. code-block:: console

    $ python manage.py import_package_configuration specs/singularity-3.6.4.json 0.16.0-1379-7a5351d495
    
    
The package is printed to the screen, along with it's full hash.


.. code-block:: console

    Filename                            specs/singularity-3.6.4.json       
    Spack Version                       0.16.0-1379-7a5351d495             
    Status                              created                            
    singularity v3.6.4                  p64nmszwer36ly7pnch5fznni4cnmndg 
    
You could run the same command externally from the container (and this extends to any command) by doing:

.. code-block:: console

    $ docker exec -it spack-monitor_uwsgi_1 python manage.py import_package_configuration specs/singularity-3.6.4.json


If you do this twice, however, it's going to tell you that it already exists.
We use the ``full_hash`` of the package to determine if it's already there.

.. code-block:: console

    $ docker exec -it spack-monitor_uwsgi_1 python manage.py import_package_configuration specs/singularity-3.6.4.json $(spack --version)
    Filename                            specs/singularity-3.6.4.json       
    Spack Version                       0.16.0-1379-7a5351d495             
    Status                              exists                             
    singularity v3.6.4                  xttimnxa2kc4rc33axvrcpzejiil6wbn   


Note that these commands will work because the working directory is ``/code`` (where the specs folder is)
and ``./code`` is bound to the host at the root of the repository.  If you need to interact
with files outside of this location, you should move them here.
Note that this interaction is intended for development or testing. If you
want to interact with the database from spack, the avenue will be via the
:ref:`getting-started_api`.

Databases
=========

By default, Spackmon will deploy with it's own postgres container, deployed
via the docker-compose.yml. If you want to downgrade to sqlite, you can
set ``USE_SQLITE`` in your ``spackmon/settings.yml`` file to a non null value.
This will save a file, ``db.sqlite3`` in your application root.
If you want to update to use a more production database, you can remove the 
``db`` section in your docker-compose.yml, and then export variables for 
your database to the environment:

.. code-block:: console

    export DATABASE_ENGINE=django.db.mysql # this is the default if you don't set it
    export DATABASE_HOST=my.hostname.dev
    export DATABASE_USER=mydatabaseuser
    export DATABASE_PASSWORD=topsecretbanana
    export DATABASE_NAME=databasename

We have developed and tested with the postgres database, so please report any issues
that you find if you try sqlite. If you want to try the application outside of the containers,
this is possible (but not developed or documented yet) so please `open an issue <https://github.com/spackmon/spack-monitor>`_.
Now that you have your container running and you've import a spec, you should
read the :ref:`getting-started_api` docs to create a user and learn how to
interact with your application in a RESTful, authenticated manner.
