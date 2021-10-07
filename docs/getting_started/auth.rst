.. _getting-started_authentication:

==============
Authentication
==============

This section will walk you through creating a user and getting your token
to authenticate you to the :ref:`getting-started_api` so you can walk through
the :ref:`getting-started_api_tutorial`. You should already have your containers
running (see :ref:`getting-started_install` if you do not).

OAuth2 Accounts
===============

To support allowing a user to create their own account, Spack Monitor has support
to login via OAauth2 from GitHub, which means that as the admin of the server
you'll need to setup an OAuth2 application, and as a user you'll need to authenticate with
GitHub to login. Setup of that requires the following.
For users to connect to Github, you need to `register a new application <https://github.com/settings/applications/new>`_ 
and export the key and secret to your environment as follows:

.. code-block:: console

    # http://psa.matiasaguirre.net/docs/backends/github.html?highlight=github
    export SOCIAL_AUTH_GITHUB_KEY='xxxxxxxxxxxxx'
    export SOCIAL_AUTH_GITHUB_SECRET='xxxxxxxxxxxxx'

To provide these secrets via docker-compose, you can add an ``environment`` section
to your yaml (that should not be placed in version control!)

.. code-block:: yaml

    uwsgi:
      restart: always
      build: .
      environment:
        - SOCIAL_AUTH_GITHUB_KEY=xxxxxxxxxxxxx
        - SOCIAL_AUTH_GITHUB_SECRET=xxxxxxxxxxxxxxxxx
      volumes:
        - .:/code
        - ./static:/var/www/static
        - ./images:/var/www/images
      links:
        - db

And then in the settings.yml, update ``ENABLE_GITHUB_AUTH`` to true. The server will
not start if the credentials are not found in the environment. When you register
the application, the callback url should be in the format `http://127.0.0.1/complete/github/`, 
and replace the localhost address with your domain. See the `Github Developers <https://github.com/settings/developers>`_ 
pages to browse more information on the Github APIs.

Legacy Account Creation
=======================

Before supporting user accounts, a user token could be generated on the command line
to associate with a build. This is still supported for anyone that doesn't want to use
(or cannot use) GitHub, however it requires a server admin to manually do the work,
which isn't ideal for all deployments. For example, if we want to add a user:

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
authenticate via the API, a flow that will generate us a temporary bearer token
(that expires after a certain amonut of time). This is the authentication
flow, discussed next.


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

If you want to interact with the API, we next recommend doing the :ref:`getting-started_api_tutorial`,
or just read more about the endpoints at :ref:`getting-started_api`.
