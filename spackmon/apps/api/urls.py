__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.conf.urls import url
from django.urls import path

from spackmon.settings import cfg
import spackmon.apps.api.views as api_views

urlpatterns = [
    path(
        "auth/token/",
        api_views.GetAuthToken.as_view(),
        name="auth_token",
    ),
    path(
        "%s/" % cfg.URL_API_PREFIX,
        api_views.ServiceInfo.as_view(),
        name="service_info",
    ),
    path(
        "%s/config/new/" % cfg.URL_API_PREFIX,
        api_views.NewConfig.as_view(),
        name="upload_config",
    ),
]


app_name = "api"
