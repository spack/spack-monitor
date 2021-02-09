__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2020-2021, Vanessa Sochat"
__license__ = "MPL 2.0"

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
]

app_name = "main"
