from django.urls import path, include
from Accounts import views as accounts_views


urlpatterns = [
    path('', include('Arrebita.urls')),
    path('accounts/', include('Accounts.urls')),
    path('perfil/', accounts_views.profile, name='profile'),
    path('login/', accounts_views.login_view, name='login'),
    path('registo/', accounts_views.register_view, name='register'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('events/', include('Events.urls')),
    path('orders/', include('Orders.urls')),
    path('statistics/', include('Statistics.urls')),
    path('wines/', include('Wines.urls')),
    path('backoffice/', include('Backoffice.urls')),
]
