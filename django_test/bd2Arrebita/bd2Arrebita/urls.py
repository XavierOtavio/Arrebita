from django.urls import path, include


urlpatterns = [
    path('', include('Arrebita.urls')),
    path('accounts/', include('Accounts.urls')),
    path('events/', include('Events.urls')),
    path('orders/', include('Orders.urls')),
    path('statistics/', include('Statistics.urls')),
    path('wines/', include('Wines.urls')),
]
