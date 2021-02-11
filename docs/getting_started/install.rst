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

Once you have these dependencies, you'll first want to build your container, which we might call `spack/spackmon`.
To do this with docker-compose:


.. code-block:: console

    $ docker-compose build
      
Once you have the base container built, you can bring it up (which also will pull
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

For this case, we want to generate and then import a custom configuration. Let's make
that first. As noted in the :ref:`development-background` section, there is a script provided
that will make it easy to generate a spec (if you don't have one handy). Let's do that first.
Since we need spack (on our host) we will run this outside of the container.
Make sure that you have exported the spack bin to your path:

.. code-block:: console

    $ export PATH=$PATH:/path/to/spack/bin


And then (if you haven't yet) clone the repository to run the generation script.
Not all examples will work, but here is one that seems to work:

.. code-block:: console

     $ git clone git@github.com:spack/spack-monitor.git
     $ cd spack-monitor
     $ mkdir -p specs
                                     # lib       # outdir
     $ ./script/generate_random_spec.py singularity specs
    ...
    wont include py-cython due to variant constraint +python
    Success! Saving to /home/vanessa/Desktop/Code/spack-monitor/specs/singularity-3.6.4.json


Your containers should already be running. Let's now shell into the container, 
where we can interact directly with the database.

.. code-block:: console
   
   $ docker exec -it spack-monitor_uwsgi_1 bash


The script ``manage.py`` provides an easy interface to run custom commands. For example,
here is how to do migrations and setup the database (this needs to be done first or manually
if you disable the commands in ``run_uwsgi.sh``:

.. code-block:: console

    $ python manage.py makemigrations main
    $ python manage.py makemigrations users
    $ python manage.py migrate
    

When the database is setup (the above commands are run, if they haven't been yet)
we can run a command to do the import:

.. code-block:: console

    $ python manage.py import_package_configuration specs/singularity-3.6.4.json
    
    
You'll then see a summary printout to the screen of the packages, versions, and hashes
that were added to the screen:


.. code-block:: console

    autoconf v2.69                      q4ep32s7zcw3kyfyemgivrxv53mqjenc   
    autoconf-archive v2019.01.06        mplalc4sz2cys2wkwzji2ltyklv7x5xf   
    automake v1.16.3                    nnrqz4c4d7hzxfsk7ptcz75wdsxm5hgw   
    berkeley-db v18.1.40                gjtqt2qiwzi5pwhial5xgbvj2ehjh7go   
    bzip2 v1.0.8                        xn4fe3zt3okv3rl24tscfuym3xxzvgll   
    cryptsetup v2.3.1                   htynr44nocgkojsjkbdnp4nfa2otmuoi   
    curl v7.74.0                        enwmyb5fojnbfdablt2gs2afixdjgort   
    diffutils v3.7                      2tm6lq6qmyrj6jjiruf7rxb3nzonnq3i   
    expat v2.2.10                       gznuc7dbmhj6xkjfhjqanemnrdxjxziq   
    gawk v5.1.0                         f4etzxppavgi2ioouyh6afkbqzxke5ql   
    gdbm v1.18.1                        jry6g36fxsyalhuthbffmla623dlqg4g   
    gettext v0.21                       gul32kw2c4abi344rzakhobej67dj53k   
    git v2.8.3                          isiszst7oeoepr6p2t77ucewp2z57qge   
    gmp v6.1.2                          qtuzif6jphtihuzkwi7cemiega7wk2db   
    go v1.14.4                          b2dgl74ooxml4zbt74rsgwfopcmttabf   
    go-bootstrap v1.4-bootstrap-20161024 tml5d3dajx7i5j3rx5h7f5vud2qigpgr   
    libiconv v1.16                      af5tdk6ilv6mah2ntgb5odryvlosijnz   
    libidn2 v2.3.0                      6pvigszeej5gqkvpp5u6cmlb4iezsqaf   
    libseccomp v2.3.3                   u2g4h3rba4be7rcvwqnbz6gn5gg5aonl   
    libsigsegv v2.12                    hbw6o4vwoewahnljakztiz5n32vy4rcz   
    libtool v2.4.6                      nijcyvdj44d7zm4mgqj3fyecnpb7vihi   
    libunistring v0.9.10                hxu7i2kt567ynjhn5oicnxfdf2aepaqa   
    libxml2 v2.9.10                     oxpxbrpqqca5hjh6blb4qv5chqqv3ykv   
    lvm2 v2.03.05                       f3l3iqzw3duerkzigowryif6fns7ok2e   
    m4 v1.4.18                          oe7xqsroqowtpv76dkdztactmnxuv3u4   
    mpfr v4.0.2                         6p34bz4swwpiemxt7ts5n7b4gvqoxfec   
    ncurses v6.2                        v3z5jtv4ztmho7onysxesbp2wqrrbn5x   
    openssh v8.4p1                      gs222i4ctitv7fl27wgnurjoqoks3e7r   
    openssl v1.1.1i                     ueylub443vmj5vq3d7ovch4gq2i2rlns   
    pcre v8.44                          3n453slowncdm66pdxxcmojvozeua7ea   
    perl v5.32.1                        fz6zjbsgnjjijfn6vtgpnjd6ldw26xqe   
    pkgconf v1.7.3                      lwcroefxaeuqfg5nshj4wl7ps4allnsy   
    popt v1.16                          cu6cp2y5iy3pdcwcbeufs3plm72o7j54   
    py-cython v0.29.21                  vtetku5vj7fxtgt5t2ry5zxjkoiagpfp   
    py-setuptools v50.3.2               vwx7qmgunfncjp5olscwa6ae2twrsq3a   
    python v3.8.7                       iyhtlgqlwybdp43edafv3nvoe3qihqqe   
    readline v8.0                       6erg6r3ryymdcoplpwglxcfvqlpqaxxc   
    shadow v4.7                         chohnmlsy6fsfbk73gzo55agxw634oq3   
    singularity v3.6.4                  o5g4ih5rauipnkuf7njvxkcp2jx5atzu   
    sqlite v3.34.0                      vlledturvidlbwwjesooknq5nes4aqcl   
    squashfs v4.4                       xslj6bhfvrzdnfijbhgmd7qc4lvzk32g   
    tar v1.32                           v2t5umv3cgfsc3fbzuzm7u7ig7gxdqq5   
    util-linux v2.36                    ancj25wbm4bqt6zw5i3h3zt3x56uhscd   
    util-linux-uuid v2.36               noev42z5uio4vav777to5kqgthwdikt5   
    xz v5.2.5                           4kcnj3oypwyyr3o46ipejwuk3x5gzrar   
    zlib v1.2.11                        sl7m27mzkbejtkrajigj3a3m37ygv4u2     
    
Wow, that's quite a lot just for Singularity! You could run the same command
externally from the container (and this extends to any command) by doing:

.. code-block:: console

    $ docker exec -it python manage.py import_package_configuration specs/singularity-3.6.4.json

Note that this will work because the working directory is ``/code`` (where the specs folder is)
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
