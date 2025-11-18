from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from .models import Order, VwOrderSummary
from .forms import OrderStatusForm
from psycopg2 import Error as PsycopgError

def order_list(request):
    orders = VwOrderSummary.objects.all()  # vista de leitura
    return render(request, "order/order_list.html", {"orders": orders})

def order_detail(request, order_id):
    # podes ler da view também, para trazer nome/email, etc.
    order = get_object_or_404(VwOrderSummary, order_id=order_id)
    return render(request, "order/order_detail.html", {"order": order})

def update_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        form = OrderStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data["status"]
            try:
                with connection.cursor() as cursor:
                    if new_status == "PAID":
                        cursor.execute("CALL update_order_to_paid(%s)", [order.order_id])
                    else:
                        # Só usa se existir mesmo esta SP. Caso não, remove.
                        cursor.execute("CALL update_order_status(%s, %s)", [order.order_id, new_status])
            except PsycopgError as e:
                # Mostra erro da BD na própria página
                form.add_error(None, f"Erro da base de dados: {e}")
                return render(request, "order/update_order.html", {"form": form, "order": order})

            return redirect("order_list")
    else:
        # valor inicial do estado a partir do registo
        form = OrderStatusForm(initial={"status": order.status})

    return render(request, "order/update_order.html", {"form": form, "order": order})
