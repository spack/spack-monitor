# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db import models
from rest_framework.authtoken.models import Token


class CustomUserManager(BaseUserManager):
    def _create_user(
        self, username, email, password, is_staff, is_superuser, **extra_fields
    ):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not username:
            raise ValueError("The given username must be set")

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            is_staff=is_staff,
            is_active=True,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(
            username, email, password, False, False, **extra_fields
        )

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True, **extra_fields)

    def add_superuser(self, user):
        """Intended for existing user"""
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def add_staff(self, user):
        """Intended for existing user"""
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    active = models.BooleanField(default=True)

    # has the user agreed to terms?
    agree_terms = models.BooleanField(default=False)
    agree_terms_date = models.DateTimeField(blank=True, default=None, null=True)

    # Ensure that we can add staff / superuser and retain on logout
    objects = CustomUserManager()

    class Meta:
        app_label = "users"
    
    @property
    def builds_count(self):
        from spackmon.apps.main.models import Build
        return Build.objects.filter(owner=self).count()

    @property
    def token(self):
        """The user token is for interaction with creating and updating workflows"""
        return str(Token.objects.get(user=self))

    def get_credentials(self, provider):
        """return one or more credentials, or None"""
        if self.is_anonymous is False:
            try:
                # Case 1: one credential
                credential = self.social_auth.get(provider=provider)
                return credential
            except:
                # Case 2: more than one credential for the provider
                credential = self.social_auth.filter(provider=provider)
                if credential:
                    return credential.last()

    def get_providers(self):
        """return a list of providers that the user has credentials for."""
        return [x.provider for x in self.social_auth.all()]

    def get_label(self):
        return "users"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create a token for the user when the user is created (with oAuth2)

    1. Assign user a token
    2. Assign user to default group

    Create a Profile instance for all newly created User instances. We only
    run on user creation to avoid having to check for existence on each call
    to User.save.

    """
    # This auth token is intended for APIs
    if created:
        Token.objects.create(user=instance)
