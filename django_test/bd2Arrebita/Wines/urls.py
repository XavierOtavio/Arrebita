# Wines/urls.py
from django.urls import path
from . import views

app_name = "wine"

urlpatterns = [
    path("", views.winelist, name="winelist"),
    path("<uuid:wine_id>/", views.wine_detail, name="wine_detail"),
]
