from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('edit/<int:order_id>/', views.update_order, name='update_order'),
    path('invoices/', views.invoice_list, name='invoice_list'),
]
