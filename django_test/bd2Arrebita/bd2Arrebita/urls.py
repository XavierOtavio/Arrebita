from django.urls import path, include
from Accounts import views as accounts_views
from Orders import views as orders_views


urlpatterns = [
    path('', include('Arrebita.urls')),
    path('accounts/', include('Accounts.urls')),
    path('perfil/', accounts_views.profile, name='profile'),
    path('login/', accounts_views.login_view, name='login'),
    path('registo/', accounts_views.register_view, name='register'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('events/', include('Events.urls')),
    path('orders/', include('Orders.urls')),
    path('cart/', orders_views.cart_view, name='cart'),
    path('cart/add/', orders_views.cart_add, name='cart_add'),
    path('cart/update/', orders_views.cart_update, name='cart_update'),
    path('cart/clear/', orders_views.cart_clear, name='cart_clear'),
    path('checkout/', orders_views.checkout, name='checkout'),
    path('checkout/sucesso/<int:order_id>/', orders_views.checkout_success, name='checkout_success'),
    path('statistics/', include('Statistics.urls')),
    path('wines/', include('Wines.urls')),
    path('backoffice/', include('Backoffice.urls')),
]
