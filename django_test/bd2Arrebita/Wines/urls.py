# Wines/urls.py
from django.urls import path
from . import views

app_name = "wine"

urlpatterns = [
    path("", views.winelist, name="winelist"),
]
