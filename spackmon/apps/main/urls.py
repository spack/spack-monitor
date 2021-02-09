__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
]

app_name = "main"
