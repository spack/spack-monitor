.. _getting-started_api:

=================================
Application Programming Interface
=================================

Spackmon implements a set of endpoints that make it possible for spack
to communicate with the database via RESTful requests. This document
outlines these endpoints, which we call the Spack Monitor Schema.

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


--------------
Authentication
--------------

Since we currently are not exposing a web interface to create accounts, etc.,
all account creation happens on the command line. For example, if we want to add
a user:

.. code-block:: console

    $ docker exec -it spack-monitor_uwsgi_1 python manage.py add_user vsoch
    Username: vsoch
    Enter Password:
    User vsoch successfully created.


You can then get your token (for the API here) as follows:


.. code-block:: console

    $ docker exec -it spack-monitor_uwsgi_1 python manage.py get_token vsoch
    Username: vsoch
    Enter Password:
    50445263afd8f67e59bd79bff597836ee6c05438


TADA! We will export this token as ``SPACKMON_TOKEN`` in the environment to
authenticate via the API, discussed next.

The Authentication Flow
=======================

We are going to use a "docker style" OAuth 2 (as described `here <https://github.com/opencontainers/distribution-spec/issues/110#issuecomment-708691114>`_, with more details provided in this section. 

The User Request
----------------

When you make a request to the API without authentication, this first request will return a 401 "Unauthorized"
`response <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/401>`_
The server knows to return a ``Www-Authenticate`` header to your client with information about how
to request a token. That might look something like:

.. ::code-block console
    
    realm="http://127.0.0.1/auth",service="http://127.0.0.1",scope="build"


Note that realm is typically referring to the authentication server, and the service is the base URL
for the monitor service. In the case of Spack Monitor they are one and the same (e.g., both on localhost) 
but this doesn't have to be the case. You'll see in the settings that you can customize
the authentication endpoint.

The requester then submits a request to the realm with those variables as query parameters (e.g., GET) 
and also provides a basic authentication header, which for Spack Monitor, is the user's username
and token associated with the account (instructions provided above for generating your username
and token). We put them together as follows:


.. ::code-block console

    "username:token"

We then base64 encode that, and add it to the http Authorization header.


.. ::code-block console

    {"Authorization": "Basic <base64 encoded username and token>"}


That request then goes to the authorization realm, which determines if the user
has permission to access the service for the scope needed. Note that scope is currently
limited to just build, and we also don't specify a specific resource. This could be
extended if needed.

The Token Generation
--------------------

Given that the user account is valid, meaning that we check that the username exists,
the token is correct, and the user has permission for the scopes requested (true by default),
we generate a jwt token that looks like the following:


.. code-block:: python

    {
      "iss": "http://127.0.0.1/auth",
      "sub": "vsoch",
      "exp": 1415387315,
      "nbf": 1415387015,
      "iat": 1415387015,
      "jti": "tYJCO1c6cnyy7kAn0c7rKPgbV1H1bFws",
      "access": [
        {
          "type": "build",
          "actions": [
            "build"
          ]
        }
      ]
    }


If you are thinking that the type and actions are redundant, you are correct.
We currently don't need to do much checking in terms of scope or actions.
The "exp" field is the timestamp for when the token expires. The nbf says "This can't be used
before this timestamp," and iat refers to the issued at timestamp. You can read more about
`jwt here <https://tools.ietf.org/html/rfc7519>`_. We basically use a python jwt library to
encode this into a long token using a secret on the server, and return this token to the 
calling client.

.. code-block:: python

    {"token": "1sdjkjf....xxsdfser", "issued_at": "<issued timestamp>", "expires_in": 600}


Retrying the Request
--------------------

The client then retries the same request, but adds the token to the Authorization header,
this time with Bearer.


.. code-block:: python

    {"Authorization": "Bearer <token>"}

And then hooray! The request should be successful, along with subsequent requests using the
token until it expires. The expiration in seconds is also defined in the settings.yml
config file. 


Disable Authentication
----------------------

You can see in the :ref:`getting-started_settings` that there is a configuration
variable to disable authentication, ``DISABLE_AUTHENTICATION``. This usually isn't recommended.
If you disable it, then views that require authentication will not look for the bearer
token in the header.

iIf you want to interact with the API, we next recommend doing the :ref:`getting-started_api_tutorial`.