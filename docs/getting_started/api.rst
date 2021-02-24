.. _getting-started_api:

=================================
Application Programming Interface
=================================

Spackmon implements a set of endpoints that make it possible for spack
to communicate with the database via RESTful requests. This document
outlines these endpoints, which we call the Spack Monitor Schema.
You should read about :ref:`getting-started_authentication` if you want
to first create a user to interact with these endpoints, and then
check out the :ref:`getting-started_api_tutorial` for a walkthrough.

--------
Overview
--------

Introduction
============

The **Spack Monitor Specification** defines an API protocol 
to standardize the requests and responses for spack to communicate with a monitoring server.
It is created in the same spirit as the `opencontainers distribution spec <https://github.com/opencontainers/distribution-spec>`_.

Definitions
===========

The following terms are used commonly in this document, and a list of definitions is provided for reference:

- **server**: a service that provides the endpoints defined in this specification
- **spack**: a local spack installation where you intend to monitor builds of software

Notational Conventions
======================

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in `RFC 2119 <http://tools.ietf.org/html/rfc2119>`_. (Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, March 1997).

Conformance
===========

Currently, we don't have any tools to test conformance, and the requirements are outlined here. 

Determining Support
===================

To check whether or not the server implements the spack monitor spec, the client SHOULD 
perform a `GET` request to the ``/ms1/`` (service info) endpoint.
If the response is ``200 OK``, then the server implements the specification. This particular endpoint
MAY be used for authentication, however authentication is outside of the scope of this spec.

For example, given a url prefix of ``http://127.0.0.0`` the client would issue a `GET`
request to:

.. code-block:: console

    GET http://127.0.0.1:5000/ms1/

And see the service info section below for more details on this request and response.
This endpoint serves to either return a successful response to the calling spack client, or
direct the client to use a differently named endpoint.

All of the following would be valid:


.. code-block:: console

    https://spack.org/ms1/
    http://spack.org/ms1/
    http://localhost/ms1/
    http://127.0.0.1/ms1/
    http://127.0.0.1:8282/ms1/


For each of the above, the client implementing the spec would be provided the url
before ``/ms1/`` (e.g., https://spack.org/) and then use that to assemble
all the endpoints (e.g., https://spack.org/ms1/).

Endpoint Requirements
=====================

Servers conforming to the Spack Monitor specification (like Spack Monitor)
must provide the following endpoints: 

 1. **Service Info** (``GET /ms1/``) endpoint with a 200 or 30* response.


Response Details
================

Generally, a response will return a json object that shows a message, and a return code. 
For example, a successful response will have a message of "success" to go along with a 200 or 201 response code,
while an unsuccessful response will have a message indicating the error, and an error
code (e.g., 400, 500, etc.). Error responses may not have data. Successful reponses 
will have metadata specific to the endpoint.

.. code-block:: python

    {"message": "success", "data" {...}, "code": 201}


Generally, endpoint data will return a lookup of objects updated or created based on the type.
For example, the new configuration endpoint has metadata about the spec created under a ``spec``
attribute of the data:

.. code-block:: python

    {
        "message": "success",
        "data": {
            "spec": {
                "full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
                "name": "singularity",
                "version": "3.6.4",
                "spack_version": "1.0.0",
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
            },
            "created": true
        },
        "code": 201
    }
    
    
Timestamps
----------

For all fields that will return a timestamp, we are tentatively going to use the stringified
version of a ``datetime.now()``, which looks like this:

.. code-block:: console
   
   2020-12-15 11:43:24.811860

Endpoint Details
================

Service Info
------------

``GET /ms1/``

This particular Endpoint exists to check the status of a running monitor service.
The client should issue a ``GET`` request to this endpoint without any data, and the response should be any of the following:

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success (indicates running)
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `302 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/302>`_: found, change namespace
- `301 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/301>`_: redirect

As the initial entrypoint, this endpoint also can communicate back to the client that the prefix (ms1)
has changed (e.g., response 302 with a Location header). More detail about the use case for each return code is provided below.
For each of the above, the minimal response returned should include in the body a status message
and a version, both strings:


.. code-block:: python

    {"status": "running", "version": "1.0.0"}

Service Info 404
''''''''''''''''

In the case of a 404 response, it means that the server does not implement the monitor spec.
The client should stop, and then respond appropriately (e.g., giving an error message or warning to the user).

.. code-block:: python

    {"status": "not implemented", "version": "1.0.0"}

Service Info 200
''''''''''''''''

A 200 is a successful response, meaning that the endpoint was found, and is running.

.. code-block:: python

    {"status": "running", "version": "1.0.0"}


Service Info 503
''''''''''''''''

If the service exists but is not running, a 503 is returned. The client should respond in the same
way as the 404, except perhaps trying later.


.. code-block:: python

    {"status": "service not available", "version": "1.0.0"}


Service Info 302
''''''''''''''''

A 302 is a special status intended to support version changes in a server. For example,
let's say that an updated specification API is served at ``/ms2/`` and by default, a client knows to
send a request to ``/ms1/``. To give the client instruction to use ``/ms2/`` for all further
interactions, the server would return a 302 response


.. code-block:: python

    {"status": "multiple choices", "version": "1.0.0"}

with a `location <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Location>`_ 
header to indicate the updated url prefix:

.. code-block:: console

    Location: /m2/

And the client would update all further prefixes accordingly.

Service Info 301
''''''''''''''''

A 301 is a more traditional redirect that is intended for one off redirects, but
not necessarily indicatig to change the entire client namespace. For example,
if the server wanted the client to redirect ``/ms1/`` to be ``/service-info/`` (but only
for this one case) the response would be:

.. code-block:: console

    {"status": "multiple choices", "version": "1.0.0"}

With a location header for just this request:


.. code-block:: console

    Location: /service-info/

For each of the above, if the server does not return a Location header, the client
should issue an error.


New Spec
--------

``POST /ms1/specs/new/``

If you have a spec configuration file, you can load it into Python and issue a request
to this endpoint. The response can be any of the following:

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented
- `201 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/201>`_: success (indicates created)
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success (but the config already exists)


New Config Created 201
''''''''''''''''''''''

If the set of specs are created from the configuration file, you'll get a 201 response with data that
includes the configuration id (the full_hash) along with full hashes
for each package included:

.. code-block:: python

    {
        "message": "success",
        "data": {
            "spec": {
                "full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
                "name": "singularity",
                "version": "3.6.4",
                "spack_version": "1.0.0",
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
            },
            "created": true
        },
        "code": 201
    }


All of the above are full hashes, which we can use as unique identifiers for the builds.


New Config Already Exists 200
'''''''''''''''''''''''''''''

If the configuration in question already exists, you'll get the same data response,
but a status code of 200 to indicate success (but not create).


New Build
---------

``POST /ms1/builds/new/``

This is the endpoint to use to get or lookup a previously done build, and retrieve
a build id that can be used for further requests.
A new build means that we have a spec, an environment, and we are starting a build!
The ``Build`` object can be either created or retrieved (if the comibination already
exists), and it will hold a reference to the spec,
the host build environment, build phases, and (if the build is successful)
a list of objects associated (e.g., libraries and other binaries produced).

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented or spec not found
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `201 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/201>`_: success
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied


In either case of success (200 or 201) the response data is formatted as follows:

.. code-block:: python

    {
        "message": "Build get or create was successful.",
        "data": {
            "build_created": true,
            "build_environment_created": true,
            "build": {
                "build_id": 1,
                "spec_full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
                "spec_name": "singularity"
            }
        },
        "code": 201
    }


New Build Created 201
'''''''''''''''''''''

When a new build is created, the status will be 201 to indicate that.

New Build Success 200
'''''''''''''''''''''

If a build is re-run, it may already have been created. The status will be 200
to indicate this.


Update Build Status
-------------------

``POST /ms1/builds/update/``

When Spack is running builds, each build task associated with a spec and host
environment can either succeed or fail, or something else. In each case,
we need to update Spack Monitor with this status. The default status for
a build task is ``NOTRUN``. Once the builds start, given a failure,
this means that the spec that failed is marked as ``FAILURE``, and the main spec 
along with the other specs that were not installed are marked as ``CANCELLED``.
In the case of success for any package, we mark with ``SUCCESS``. If Spack has a setting
to "rollback" we will need to account for that (not currently implemented).

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented or spec not found
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied


Build Task Updated 200
''''''''''''''''''''''

When you want to update the status of a spec build, a successful update will
return a 200 response.


.. code-block:: python

    {
        "message": "Status updated",
        "data": {
            "build": {
                "build_id": 1,
                "spec_full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
                "spec_name": "singularity"
            }
        },
        "code": 200
    }


Update Build Phase
------------------

``POST /ms1/builds/phases/update/``

Build Phases are associated with builds, and this is when we have output and error
files. The following responses re valid:

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented or spec not found
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied

The request to update the phase should look like the following - we include
the build id (created or retrieved from the get build endpoint) along with simple
metadata about the phase, and a status.

.. code-block:: python

    {
        "build_id": 47,
        "status": "SUCCESS",
        "output": null,
        "phase_name": "autoreconf"
    }



Update Build Phase 200
''''''''''''''''''''''

When a build phase is successfully updated, the response data looks like the following:


.. code-block:: python

    {
        "message": "Phase autoconf was successfully updated.",
        "code": 200,
        "data": {
            "build_phase": {
                "id": 1,
                "status": "SUCCESS",
                "name": "autoconf"
            }
        }
    }


Builds Metadata
---------------

``POST /ms1/builds/metadata/``

When a spec is finished installing, we have a metadata folder, usually within
the spack root located at ``opt/<system>/<compiler>/<package>/.spack`` 
with one or more of the following files:

 - spack-configure-args.txt'
 - spack-build-env.txt'
 - spec.yaml
 - archived-files
 - spack-build-out.txt
 - install_manifest.json
 - repos
 - errors.txt
 
We want to send build environment and install files from this location, so
the client within spack can read and parse files. The data should be formatted as follows:

.. code-block:: python

    {
        "environ": {
            "SPACK_CC": "/usr/bin/gcc",
            "SPACK_CC_RPATH_ARG": "-Wl,-rpath,",
            "SPACK_COMPILER_SPEC": "gcc@9.3.0",
            "SPACK_CXX": "/usr/bin/g++",
            "SPACK_CXX_RPATH_ARG": "-Wl,-rpath,",
            ...
            "SPACK_TARGET_ARGS": "'-march=skylake -mtune=skylake'"
        },
        "config": "",
        "manifest": {
            "/home/vanessa/Desktop/Code/spack/opt/spack/linux-ubuntu20.04-skylake/gcc-9.3.0/diffutils-3.7-2tm6lq6qmyrj6jjiruf7rxb3nzonnq3i/.spack": {
                "mode": 17901,
                "owner": 1000,
                "group": 1000,
                "type": "dir"
            },
            ...
            "/home/vanessa/Desktop/Code/spack/opt/spack/linux-ubuntu20.04-skylake/gcc-9.3.0/diffutils-3.7-2tm6lq6qmyrj6jjiruf7rxb3nzonnq3i": {
                "mode": 17901,
                "owner": 1000,
                "group": 1000,
                "type": "dir"
            }
        },
        "full_hash": "5wdhxf5usk7g6gznwhydbwzmdibxqhjp"
    }


We don't represent output here, as it's captured and stored with ``BuildPhase`` objects.
The environment is read in, filtered
to a list to include only ``SPACK_*`` variables, and split into key value pairs,
and the package full hash is provided to look up. If any information does not
exist, it is simply not sent. A full request might look like the following:
The response can then be any of the following:

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success

Unlike other endpoints, this one does not check if data is already added for the
build, it simply re-writes it. This is under the assumption that we might re-do
a build and update the metadata associated. The response is brief and tells the 
user that the metadata for the build has been updated:

.. code-block:: python

    {
        "message": "Metadata updated",
        "data": {
            "build": {
                "build_id": 1,
                "spec_full_hash": "p64nmszwer36ly7pnch5fznni4cnmndg",
                "spec_name": "singularity"
            }
        },
        "code": 200
    }
