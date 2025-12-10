from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.dashboard, name="backoffice_dashboard"),

    # lista de vinhos no backoffice
    path(
        "wines/",
        views.backoffice_wines,
        name="backoffice_wines",
    ),

    path(
        "wines/",
        views.backoffice_wine_create,
        name="backoffice_wine_create",
    ),

    # apagar vinho
    path(
        "wines/<uuid:wine_id>/delete/",
        views.backoffice_wine_delete,
        name="backoffice_wine_delete",
    ),
]
