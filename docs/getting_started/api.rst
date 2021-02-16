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

Successful Responses
--------------------

Generally, a successful response will return a json object that shows a message
with "success" along with a data object with metadata specific to the endpoint.

.. code-block:: python

    {"message": "success", "data" {...}}



Errors
------

For all error responses, the server can (OPTIONAL) return in the body a nested structure of errors,
each including a message and error code. For example:


.. code-block:: python

    {
        "errors": [
            {
                "code": "<error code>",
                "message": "<error message>",
                "detail": ...
            },
            ...
        ]
    }


Currently we don't have a namespace for errors, but this can be developed if/when needed.
For now, the code can be a standard server error code.

Timestamps
----------

For all fields that return a timestamp, we are tentatively going to use the stringified
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


New Config
----------

``POST /ms1/config/new/``

If you have a configuration file, you can load it into Python and issue a request
to this endpoint. The response can be any of the following:

- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented
- `201 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/201>`_: success (indicates created)
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request
- `403 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403>`_: permission denied
- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success (but the config already exists)


New Config Created 201
''''''''''''''''''''''

If the configuration is created, you'll get a 201 response with data that
includes the configuration id (the full_hash) along with full hashes
for each package included:

.. code-block:: python

    {
        "message": "success",
        "data": {
            "full_hash": "hxkll3hd7eb7qp7oos4utjjyjq7v3kek",
            "packages": {
                "autoconf": "qobbaw2iiotqd6zllbmckbxacw6h2ivk",
                "m4": "nhqxxeekukxwmss7juovorh74liclysw",
                "libsigsegv": "r2wa677ntwzamepabphbhwfyikiyg37j",
                "perl": "bcivb4krzgesrlcdhsz6k5ul3vlzdd7w",
                "berkeley-db": "la233dfen54tshpywjqhjq446j7o4hqr",
                "gdbm": "fjy3imkxjkvqemteo2pysxmuwfb32ely",
                "readline": "gml7funyikp2tu4ngg4jiexp6otysay4",
                "ncurses": "zuimpjfdx7gd6o3xhhzqekxazfgdgivh",
                "pkgconf": "faqkgt22jrp7wnmqal5zsl7olisc22qk",
                "automake": "y2mlu7ou6wx54i5qwagrviy2foeefaho",
                "libiconv": "qhvlpedcedmc7akojaftw46i5daybsfr",
                "libxml2": "o5bqxfuieaf37mc2gdvnfdqqthzpbmis",
                "xz": "w7qivbfd35zjgjavs6kl36yhl6oev75y",
                "libtool": "witmr33yv7xogeaxyynobdblkuzwenwr",
                "openssl": "u3aemyff3aw4nnh3igoyktpwukal3zjv",
                "zlib": "nfa3orbnlq6az76gfdesjmej62pvjh7x",
                "hdf5": "hxkll3hd7eb7qp7oos4utjjyjq7v3kek",
                "util-macros": "yeype6hteniz6bj3ec4dt2evcvslxi63",
                "libevent": "xcvquzui2mjux3hg2qarpbwv42u6cnfv",
                "openmpi": "pekjjw3a5qbgwfwktvv3jqie4veeq7m6",
                "numactl": "bvjlcnxyyumevwp2wvc3ht2uudje7owh",
                "hwloc": "vifktdoq6zle3rfjplmzxoltht5iral5",
                "libpciaccess": "rr2nr5f4lxs53onoycnq47j7yhygibg2"
            }
        }
    }


New Config Already Exists 200
'''''''''''''''''''''''''''''

If the configuration in question already exists, you'll get the same data response,
but a status code of 200 to indicate success (but not create).


