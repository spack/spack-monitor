__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.conf.urls import url
from django.urls import path

from spackmon.settings import cfg
import spackmon.apps.api.views as api_views
from .permissions import AllowAnyGet

urlpatterns = [
    path(
        "ms1/",
        api_views.ServiceInfo.as_view(),
        name="service_info",
    ),
]


app_name = "api"
