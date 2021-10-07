# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from django.contrib.auth import logout as auth_logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from ratelimit.decorators import ratelimit
from django.utils import timezone
from django.http import JsonResponse
from social_core.backends.github import GithubOAuth2
from six.moves.urllib.parse import urljoin

from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
    cfg,
)


def logout(request):
    """log the user out, either from the notebook or traditional Django auth"""
    try:
        del request.session["user_id"]
    except KeyError:
        pass
    auth_logout(request)

    # A traditional Django authentication is here
    return redirect("/")


def validate_credentials(user, context=None):
    """
    Validate a user credentials.

    Validate_credentials will return a context object with "aok" for each credential
    that exists, and "None" if it does not for a given user

    Parameters
    ==========
    user: the user to check, should have social_auth
    context: an optional context object to append to
    """
    if context is None:
        context = dict()

    # Right now we have github for repos and google for storage
    credentials = [
        {"provider": "google-oauth2", "key": "google_credentials"},
        {"provider": "github", "key": "github_credentials"},
        {"provider": "globus", "key": "globus_credentials"},
        {"provider": "twitter", "key": "twitter_credentials"},
    ]

    # Iterate through credentials, and set each available to aok. This is how
    # the templates will know to tell users which they need to add, etc.
    credentials_missing = "aok"
    for group in credentials:
        credential = None
        if not user.is_anonymous:
            credential = user.get_credentials(provider=group["provider"])
        if credential is not None:
            context[group["key"]] = "aok"
        else:
            credentials_missing = None

    # This is a global variable to indicate all credentials good
    context["credentials"] = credentials_missing
    return context


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def login(request, message=None):
    """
    Login a user.
    """
    if message is not None:
        messages.info(request, message)

    context = None
    if request.user.is_authenticated:
        context = validate_credentials(user=request.user)
    return render(request, "social/login.html", context)


################################################################################
# SOCIAL AUTH
################################################################################


def redirect_if_no_refresh_token(backend, response, social, *args, **kwargs):
    """http://python-social-auth.readthedocs.io/en/latest/use_cases.html#re-prompt-google-oauth2-users-to-refresh-the-refresh-token"""
    if (
        backend.name == "google-oauth2"
        and social
        and response.get("refresh_token") is None
        and social.extra_data.get("refresh_token") is None
    ):
        return redirect("/login/google-oauth2?approval_prompt=force")


## Ensure equivalent email across accounts


def social_user(backend, uid, user=None, *args, **kwargs):
    """OVERRIDED: It will give the user an error message if the
    account is already associated with a username."""
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)

    if social:
        if user and social.user != user:
            msg = "This {0} account is already in use.".format(provider)
            return login(request=backend.strategy.request, message=msg)
            # raise AuthAlreadyAssociated(backend, msg)
        elif not user:
            user = social.user

    return {
        "social": social,
        "user": user,
        "is_new": user is None,
        "new_association": social is None,
    }
