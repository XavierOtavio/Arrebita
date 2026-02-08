from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('edit/<int:order_id>/', views.update_order, name='update_order'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('pay/<int:order_id>/', views.pay_order, name='pay_order'),
]
