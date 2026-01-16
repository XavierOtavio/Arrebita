from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from .models import Order
from .forms import OrderForm


def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'order/order_list.html', {'orders': orders})


def update_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    form = OrderForm(request.POST or None, initial_order=order)

    if request.method == "POST" and form.is_valid():

        data = form.cleaned_data

        with connection.cursor() as cursor:
            cursor.execute("""
                CALL public.update_order_full(
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, [
                order_id,
                data.get('order_number'),
                data.get('user_id'),
                data.get('kind'),
                data.get('status'),
                data.get('billing_name'),
                data.get('billing_nif'),
                data.get('billing_address'),
                data.get('invoice_url'),
            ])

        return redirect('order_list')

    return render(request, 'order/update_order.html', {
        'form': form,
        'order': order
    })


def invoice_list(request):
    from .models import Invoice
    invoices = Invoice.objects.all().order_by('-issued_at')
    return render(request, 'order/invoice_list.html', {'invoices': invoices})
