from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    # Dashboard principal
    path(
        "",
        views.dashboard,
        name="backoffice_dashboard",
    ),

    # Lista de vinhos (GET com filtros)
    path(
        "wines/",
        views.backoffice_wines,
        name="backoffice_wines",
    ),

    # Criar novo vinho (POST)
    path(
        "wines/create/",
        views.backoffice_wine_create,
        name="backoffice_wine_create",
    ),

    # Atualizar vinho existente (POST a partir do modal Editar)
    path(
        "wines/<uuid:wine_id>/update/",
        views.backoffice_wine_update,
        name="backoffice_wine_update",
    ),

    # Apagar vinho (POST)
    path(
        "wines/<uuid:wine_id>/delete/",
        views.backoffice_wine_delete,
        name="backoffice_wine_delete",
    ),

    # Criar imagem para um vinho (POST)
    path(
        "wines/<uuid:wine_id>/images/create/",
        views.backoffice_wine_image_create,
        name="backoffice_wine_image_create",
    ),

    # Apagar imagem de um vinho (POST)
    path(
        "wines/<uuid:wine_id>/images/<uuid:image_id>/delete/",
        views.backoffice_wine_image_delete,
        name="backoffice_wine_image_delete",
    ),
]
