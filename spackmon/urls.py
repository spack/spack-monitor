# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

from spackmon.apps.base import urls as base_urls
from spackmon.apps.main import urls as main_urls
from spackmon.apps.users import urls as user_urls
from spackmon.apps.api import urls as api_urls

admin.site.site_header = "spackmon Admin"
admin.site.site_title = "spackmon Admin"
admin.site.index_title = "spackmon Admin"

# Configure custom error pages
handler404 = "spackmon.apps.base.views.handler404"
handler500 = "spackmon.apps.base.views.handler500"

admin.autodiscover()

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^", include(base_urls, namespace="base")),
    url(r"^", include(api_urls, namespace="api")),
    url(r"^", include(main_urls, namespace="main")),
    url(r"^", include(user_urls, namespace="users")),
    url(
        r"^robots\.txt?/$",
        TemplateView.as_view(
            template_name="base/robots.txt", content_type="text/plain"
        ),
    ),
]
