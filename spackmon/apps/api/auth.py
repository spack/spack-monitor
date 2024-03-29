# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.urls import resolve
from django.contrib.auth import get_user_model

from spackmon.settings import cfg

from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from django.middleware import cache

from datetime import datetime
import uuid
import base64
import re
import time
import jwt


User = get_user_model()


def get_server(request):
    """Given a request, parse it to determine the server name and using http/https"""
    scheme = request.is_secure() and "https" or "http"
    return f"{scheme}://{request.get_host()}"


def is_authenticated(request, scopes=None):
    """
    Function to check if a request is authenticated, the request is required.
    If there are more scoped permissions in the future, we can adopt this
    function to require detail about this scope. For now we assume that
    the user with a token has permission to interact with the build API.
    We return a boolean to indicate if the user is authenticated, and
    a response with the challenge if not.

    Arguments:
    ==========
    request (requests.Request)    : the Request object to inspect
    scopes              (list)    : a list of scopes (defaults to [build])
    """
    # Scopes default to build
    scopes = scopes or ["build"]

    # Derive the view name from the request PATH_INFO
    func, two, three = resolve(request.META["PATH_INFO"])
    view_name = "%s.%s" % (func.__module__, func.__name__)

    # If authentication is disabled, return the original view
    if cfg.DISABLE_AUTHENTICATION or view_name not in settings.AUTHENTICATED_VIEWS:
        return True, None, None

    # Case 1: Already has a jwt valid token
    is_valid, user = validate_jwt(request)
    if is_valid:
        return True, None, user

    # Case 2: Response will return request for auth
    user = get_user(request)
    if not user:
        headers = {"Www-Authenticate": get_challenge(request, scopes=scopes)}
        return False, Response(status=401, headers=headers), user

    # Denied for any other reason
    return False, Response(status=403), user


def generate_jwt(username, scope, realm):
    """Given a username, scope, realm, repository, and service, generate a jwt
    token to return to the user with a default expiration of 10 minutes.

    Arguments:
    ==========
    username (str)  : the user's username to add under "sub"
    scope (list)    : a list of scopes to require (e.g., ['build'])
    realm (str)     : the authentication realm, typically <server>/auth
    """
    # The jti expires after TOKEN_EXPIRES_SECONDS
    issued_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    filecache = cache.caches["spackmon_api"]
    jti = str(uuid.uuid4())
    filecache.set(jti, "good", timeout=cfg.API_TOKEN_EXPIRES_SECONDS)
    now = int(time.time())
    expires_at = now + cfg.API_TOKEN_EXPIRES_SECONDS

    # import jwt and generate token
    # https://tools.ietf.org/html/rfc7519#section-4.1.5
    payload = {
        "iss": realm,  # auth endpoint
        "sub": username,
        "exp": expires_at,
        "nbf": now,
        "iat": now,
        "jti": jti,
        "access": [{"type": "build", "actions": scope}],
    }
    token = jwt.encode(payload, settings.JWT_SERVER_SECRET, algorithm="HS256")
    return {
        "token": token,
        "expires_in": cfg.API_TOKEN_EXPIRES_SECONDS,
        "issued_at": issued_at,
    }


def validate_jwt(request):
    """Given a jwt token, decode and validate

    Arguments:
    ==========
    request (requests.Request)    : the Request object to inspect
    """
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if re.search("bearer", header, re.IGNORECASE):
        encoded = re.sub("bearer", "", header, flags=re.IGNORECASE).strip()

        # Any reason not valid will issue an error here
        try:
            decoded = jwt.decode(
                encoded, settings.JWT_SERVER_SECRET, algorithms=["HS256"]
            )
        except Exception as exc:
            print("jwt could no be decoded, %s" % exc)
            return False, None

        # Ensure that the jti is still valid
        filecache = cache.caches["spackmon_api"]
        if not filecache.get(decoded.get("jti")) == "good":
            print("jwt not found in cache.")
            return False, None

        # The user must exist
        try:
            user = User.objects.get(username=decoded.get("sub"))
            return True, user

        except User.DoesNotExist:
            print("Username %s not found" % decoded.get("sub"))
            return False, None

        # TODO: any validation needed for access type or permissions?

    return False, None


def get_user(request):
    """Given a request, read the Authorization header to get the base64 encoded
    username and token (password) which is a basic auth. If we return the user
    object, the user is successfully authenticated. Otherwise, return None.
    and the calling function should return Forbidden status.

    Arguments:
    ==========
    request (requests.Request)    : the Request object to inspect
    """
    header = request.META.get("HTTP_AUTHORIZATION", "")

    if re.search("basic", header, re.IGNORECASE):
        encoded = re.sub("basic", "", header, flags=re.IGNORECASE).strip()
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, token = decoded.split(":", 1)
        try:
            token = Token.objects.get(key=token)
            if token.user.username == username:
                return token.user
        except:
            pass


def get_token(request):
    """The same as validate_token, but return the token object to check the
    associated user.

    Arguments:
    ==========
    request (requests.Request)    : the Request object to inspect
    """
    # Coming from HTTP, look for authorization as bearer token
    token = request.META.get("HTTP_AUTHORIZATION")

    if token:
        try:
            return Token.objects.get(key=token.replace("BEARER", "").strip())
        except Token.DoesNotExist:
            pass

    # Next attempt - try to get token via user session
    elif request.user.is_authenticated and not request.user.is_anonymous:
        try:
            return Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            pass


def get_challenge(request, scopes=["build"]):
    """Given an unauthenticated request, return a challenge in
    the Www-Authenticate header

    Arguments:
    ==========
    request (requests.Request): the Request object to inspect
    repository (str)          : the repository name
    scopes (list)             : list of scopes to return
    """
    DOMAIN_NAME = get_server(request)
    if not isinstance(scopes, list):
        scopes = [scopes]
    auth_server = cfg.AUTH_SERVER or "%s/auth/token/" % DOMAIN_NAME
    return 'realm="%s",service="%s",scope="%s"' % (
        auth_server,
        DOMAIN_NAME,
        ",".join(scopes),
    )
