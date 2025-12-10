from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from .models import Order
from .forms import OrderStatusForm
from .models import Invoice



def order_list(request):
    orders = Order.objects.all()

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")

        if order_id and new_status:
            with connection.cursor() as cursor:
                cursor.execute("CALL public.update_order(%s, %s)", [order_id, new_status])

            return redirect('order_list')

    return render(request, 'order/order_list.html', {'orders': orders})

def update_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)  # Buscar a ordem pela ID
    form = OrderStatusForm(request.POST or None, instance=order)

    if form.is_valid():
        updated_order = form.save()

        if updated_order.status == 'PAID':
            with connection.cursor() as cursor:
                cursor.execute("CALL public.update_order(%s)", [updated_order.order_id])

        return redirect('order_list')  # Redireciona para a lista de ordens

    return render(request, 'order/update_order.html', {'form': form, 'order': order})

def invoice_list(request):
    invoices = Invoice.objects.filter(order__status='PAID')

    return render(request, 'order/invoice_list.html', {'invoices': invoices})
