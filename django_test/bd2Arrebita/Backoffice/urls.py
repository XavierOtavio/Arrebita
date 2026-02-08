from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    # Dashboard principal
    path(
        "",
        views.dashboard,
        name="dashboard",
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

    # Lista de eventos (GET com filtros)
    path(
        "events/",
        views.backoffice_events,
        name="backoffice_events",
    ),

    # Criar novo evento (POST)
    path(
        "events/create/",
        views.backoffice_event_create,
        name="backoffice_event_create",
    ),

    # Atualizar evento (POST)
    path(
        "events/<uuid:event_id>/update/",
        views.backoffice_event_update,
        name="backoffice_event_update",
    ),

    # Exportar eventos (GET)
    path(
        "events/export/",
        views.backoffice_events_export,
        name="backoffice_events_export",
    ),

    # Importar eventos (POST)
    path(
        "events/import/",
        views.backoffice_events_import,
        name="backoffice_events_import",
    ),

    # Apagar evento (POST)
    path(
        "events/<uuid:event_id>/delete/",
        views.backoffice_event_delete,
        name="backoffice_event_delete",
    ),

    # Lista de utilizadores (GET)
    path(
        "users/",
        views.backoffice_users,
        name="backoffice_users",
    ),

    # Criar utilizador (POST)
    path(
        "users/create/",
        views.backoffice_user_create,
        name="backoffice_user_create",
    ),

    # Atualizar utilizador (POST)
    path(
        "users/<int:user_id>/update/",
        views.backoffice_user_update,
        name="backoffice_user_update",
    ),

    # Acessos por utilizador (GET/POST)
    path(
        "users/access/",
        views.backoffice_user_access,
        name="backoffice_user_access",
    ),
]
