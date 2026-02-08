from decimal import Decimal
import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from django.http import HttpResponse
from django.utils import timezone

from Wines.models import WineListView
from Events.models import EventListView
from .models import Order, Invoice
from .forms import OrderForm
from .pdf_utils import build_invoice_pdf


def _get_cart(request):
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    if "wines" in cart or "events" in cart:
        wines = cart.get("wines", {})
        events = cart.get("events", {})
    else:
        wines = cart
        events = {}

    def _clean_bucket(bucket):
        cleaned = {}
        if not isinstance(bucket, dict):
            return cleaned
        for item_id, qty in bucket.items():
            try:
                qty_value = int(qty)
            except (TypeError, ValueError):
                continue
            if qty_value > 0:
                cleaned[str(item_id)] = qty_value
        return cleaned

    cleaned_cart = {
        "wines": _clean_bucket(wines),
        "events": _clean_bucket(events),
    }

    if cart != cleaned_cart:
        request.session["cart"] = cleaned_cart

    return cleaned_cart


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _wine_unit_price(wine):
    if wine.has_active_promo and wine.promo_price is not None:
        return wine.promo_price
    return wine.price or Decimal("0")


def _event_display_title(event):
    title = (event.title or "").strip()
    slug = (event.slug or "").strip()
    if title:
        return title
    if slug:
        return slug.replace("-", " ").title()
    return f"Evento {event.event_id}"


def _event_location(event):
    if event.is_online:
        return "Online"
    parts = []
    if event.venue_name:
        parts.append(event.venue_name)
    city_parts = [event.city, event.region, event.country_code]
    city_line = ", ".join([part for part in city_parts if part])
    if city_line:
        parts.append(city_line)
    return " - ".join(parts)


def _event_unit_price(event):
    if event.is_free:
        return Decimal("0")
    if event.price_cents is None:
        return Decimal("0")
    return (Decimal(event.price_cents) / Decimal("100")).quantize(Decimal("0.01"))


def _cart_items(cart):
    wines_bucket = cart.get("wines", {}) if isinstance(cart, dict) else {}
    events_bucket = cart.get("events", {}) if isinstance(cart, dict) else {}

    wine_ids = list(wines_bucket.keys())
    event_ids = list(events_bucket.keys())

    wines = WineListView.objects.filter(wine_id__in=wine_ids)
    wine_map = {str(wine.wine_id): wine for wine in wines}

    events = EventListView.objects.filter(event_id__in=event_ids)
    event_map = {str(event.event_id): event for event in events}

    items = []
    total = Decimal("0")
    items_count = 0

    for wine_id, qty in wines_bucket.items():
        wine = wine_map.get(str(wine_id))
        if not wine:
            continue
        unit_price = _wine_unit_price(wine)
        line_total = unit_price * qty
        items.append(
            {
                "kind": "wine",
                "wine": wine,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )
        total += line_total
        items_count += qty

    for event_id, qty in events_bucket.items():
        event = event_map.get(str(event_id))
        if not event:
            continue
        event.display_title = _event_display_title(event)
        event.location_display = _event_location(event)
        unit_price = _event_unit_price(event)
        line_total = unit_price * qty
        items.append(
            {
                "kind": "event",
                "event": event,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )
        total += line_total
        items_count += qty

    return items, total, items_count


def _enum_values(enum_name):
    with connection.cursor() as cur:
        cur.execute(f"SELECT unnest(enum_range(NULL::public.{enum_name}))::text;")
        return [row[0] for row in cur.fetchall()]


def _pick_enum_value(values, preferred):
    for candidate in preferred:
        if candidate in values:
            return candidate
    return values[0] if values else None


def _resolve_paid_status(values):
    for candidate in ("paid", "pago", "confirmed"):
        if candidate in values:
            return candidate
    return None


def _generate_order_number():
    date_str = timezone.now().strftime("%Y%m%d")
    for _ in range(6):
        suffix = uuid.uuid4().hex[:6].upper()
        number = f"ORD-{date_str}-{suffix}"
        if not Order.objects.filter(order_number=number).exists():
            return number
    return f"ORD-{date_str}-{uuid.uuid4().hex[:8].upper()}"


def _replace_order_items(order_id, items):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM public.order_items WHERE order_id = %s;", [order_id])
        for item in items:
            cur.execute(
                """
                INSERT INTO public.order_items (order_id, wine_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (order_id, wine_id)
                DO UPDATE SET quantity = EXCLUDED.quantity;
                """,
                [order_id, item["wine_id"], item["quantity"]],
            )


def _ensure_event_items_table():
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS public.order_event_items (
                    order_event_item_id integer GENERATED ALWAYS AS IDENTITY,
                    order_id integer NOT NULL,
                    event_id uuid NOT NULL,
                    quantity integer NOT NULL,
                    CONSTRAINT order_event_items_pkey PRIMARY KEY (order_event_item_id),
                    CONSTRAINT order_event_items_order_id_fkey
                        FOREIGN KEY (order_id)
                        REFERENCES public.orders (order_id)
                        ON DELETE CASCADE,
                    CONSTRAINT order_event_items_event_id_fkey
                        FOREIGN KEY (event_id)
                        REFERENCES public.events (event_id)
                        ON DELETE RESTRICT,
                    CONSTRAINT order_event_items_quantity_ck
                        CHECK (quantity > 0),
                    CONSTRAINT order_event_items_order_event_uk
                        UNIQUE (order_id, event_id)
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_order_event_items_order_id ON public.order_event_items (order_id);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_order_event_items_event_id ON public.order_event_items (event_id);"
            )
        return True
    except Exception:
        return False


def _replace_order_event_items(order_id, items):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM public.order_event_items WHERE order_id = %s;", [order_id])
        for item in items:
            cur.execute(
                """
                INSERT INTO public.order_event_items (order_id, event_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (order_id, event_id)
                DO UPDATE SET quantity = EXCLUDED.quantity;
                """,
                [order_id, item["event_id"], item["quantity"]],
            )


def cart_view(request):
    cart = _get_cart(request)
    items, total, items_count = _cart_items(cart)
    return render(
        request,
        "cart.html",
        {
            "items": items,
            "total": total,
            "items_count": items_count,
        },
    )


def cart_add(request):
    if request.method != "POST":
        return redirect("/cart/")

    item_type = (request.POST.get("item_type") or "wine").strip().lower()
    item_id = (
        request.POST.get("item_id")
        or request.POST.get("wine_id")
        or request.POST.get("event_id")
        or ""
    ).strip()
    qty_raw = (request.POST.get("qty") or "1").strip()
    next_url = (request.POST.get("next") or "").strip()

    try:
        qty = int(qty_raw)
    except (TypeError, ValueError):
        qty = 1
    if qty <= 0:
        qty = 1

    if item_type not in {"wine", "event"}:
        item_type = "wine"

    if not item_id:
        return redirect(next_url or "/cart/")

    cart = _get_cart(request)
    bucket = cart["events"] if item_type == "event" else cart["wines"]
    bucket[item_id] = bucket.get(item_id, 0) + qty
    _save_cart(request, cart)

    return redirect(next_url or "/cart/")


def cart_update(request):
    if request.method != "POST":
        return redirect("/cart/")

    cart = _get_cart(request)
    remove_id = (request.POST.get("remove_id") or "").strip()
    if remove_id:
        if remove_id.startswith("wine:"):
            cart["wines"].pop(remove_id.split(":", 1)[1], None)
        elif remove_id.startswith("event:"):
            cart["events"].pop(remove_id.split(":", 1)[1], None)

    for wine_id in list(cart["wines"].keys()):
        qty_raw = request.POST.get(f"qty_wine_{wine_id}")
        if qty_raw is None:
            continue
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            qty = 1
        cart["wines"][wine_id] = qty

    for event_id in list(cart["events"].keys()):
        qty_raw = request.POST.get(f"qty_event_{event_id}")
        if qty_raw is None:
            continue
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            qty = 1
        cart["events"][event_id] = qty

    _save_cart(request, cart)
    next_url = (request.POST.get("next") or "").strip()
    if next_url.startswith("/checkout"):
        return redirect(next_url)
    return redirect("/cart/")


def cart_clear(request):
    if request.method == "POST":
        _save_cart(request, {"wines": {}, "events": {}})
    return redirect("/cart/")


def checkout(request):
    user = getattr(request, "current_user", None)
    if not user:
        return redirect("/login/?next=/checkout/")

    cart = _get_cart(request)
    items, total, items_count = _cart_items(cart)
    if not items:
        return redirect("/cart/")

    wine_items = [item for item in items if item.get("kind") == "wine"]
    event_items = [item for item in items if item.get("kind") == "event"]

    error = ""
    billing_name_value = getattr(user, "full_name", "") if user else ""
    billing_nif_value = ""
    billing_address_value = ""

    if request.method == "POST":
        billing_name = (request.POST.get("billing_name") or "").strip()
        billing_nif = (request.POST.get("billing_nif") or "").strip() or None
        billing_address = (request.POST.get("billing_address") or "").strip()
        pay_now = (request.POST.get("pay_now") or "1").strip() == "1"

        billing_name_value = billing_name
        billing_nif_value = billing_nif or ""
        billing_address_value = billing_address

        if not billing_name or not billing_address:
            error = "Preenche nome e morada para validar a encomenda."
        else:
            if event_items and not _ensure_event_items_table():
                error = "Nao foi possivel registar bilhetes neste momento."
            if error:
                return render(
                    request,
                    "checkout.html",
                    {
                        "items": items,
                        "total": total,
                        "items_count": items_count,
                        "error": error,
                        "billing_name": billing_name_value,
                        "billing_nif": billing_nif_value,
                        "billing_address": billing_address_value,
                        "billing_email": getattr(user, "email", ""),
                    },
                )

            status_values = _enum_values("order_status")
            kind_values = _enum_values("order_kind")

            paid_status = _resolve_paid_status(status_values)
            if pay_now and paid_status:
                status = paid_status
            else:
                status = _pick_enum_value(
                    status_values,
                    ["pending", "new", "draft", "paid", "pago", "confirmed"],
                )

            if event_items and wine_items:
                kind_pref = ["mixed", "bundle", "combo"]
            elif event_items:
                kind_pref = ["event", "ticket", "online", "web"]
            else:
                kind_pref = ["wine", "store", "online", "web"]

            kind = _pick_enum_value(kind_values, kind_pref)

            order_number = _generate_order_number()
            user_id = user.user_id if user else None

            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.orders (
                        order_number,
                        user_id,
                        kind,
                        status,
                        billing_name,
                        billing_nif,
                        billing_address
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING order_id;
                    """,
                    [
                        order_number,
                        user_id,
                        kind,
                        status,
                        billing_name,
                        billing_nif,
                        billing_address,
                    ],
                )
                row = cur.fetchone()

            if row:
                order_id = row[0]
                if wine_items:
                    order_items = [
                        {"wine_id": item["wine"].wine_id, "quantity": item["quantity"]}
                        for item in wine_items
                    ]
                    _replace_order_items(order_id, order_items)
                if event_items:
                    order_event_items = [
                        {"event_id": item["event"].event_id, "quantity": item["quantity"]}
                        for item in event_items
                    ]
                    _replace_order_event_items(order_id, order_event_items)

                _save_cart(request, {"wines": {}, "events": {}})
                return redirect(f"/checkout/sucesso/{order_id}/")

            error = "Nao foi possivel validar a encomenda."

    return render(
        request,
        "checkout.html",
        {
            "items": items,
            "total": total,
            "items_count": items_count,
            "error": error,
            "billing_name": billing_name_value,
            "billing_nif": billing_nif_value,
            "billing_address": billing_address_value,
            "billing_email": getattr(user, "email", ""),
        },
    )


def checkout_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    invoice = Invoice.objects.filter(order_id=order_id).first()

    items = []
    total = Decimal("0")
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT oi.wine_id, oi.quantity, w.name, w.price
                FROM public.order_items oi
                LEFT JOIN public.vw_wine_list w ON w.wine_id = oi.wine_id
                WHERE oi.order_id = %s
                ORDER BY w.name NULLS LAST;
                """,
                [order_id],
            )
            for row in cur.fetchall():
                unit_price = Decimal(str(row[3] or 0))
                line_total = unit_price * row[1]
                total += line_total
                items.append(
                    {
                        "kind": "wine",
                        "wine_id": row[0],
                        "quantity": row[1],
                        "title": row[2],
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )
    except Exception:
        items = []

    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT oe.event_id, oe.quantity, e.title, e.price_cents, e.is_free
                FROM public.order_event_items oe
                LEFT JOIN public.events e ON e.event_id = oe.event_id
                WHERE oe.order_id = %s
                ORDER BY e.title NULLS LAST;
                """,
                [order_id],
            )
            for row in cur.fetchall():
                if row[4]:
                    unit_price = Decimal("0")
                elif row[3] is not None:
                    unit_price = Decimal(row[3]) / Decimal("100")
                else:
                    unit_price = Decimal("0")
                line_total = unit_price * row[1]
                total += line_total
                items.append(
                    {
                        "kind": "event",
                        "event_id": row[0],
                        "quantity": row[1],
                        "title": row[2] or str(row[0]),
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )
    except Exception:
        pass

    status_values = _enum_values("order_status")
    paid_status = _resolve_paid_status(status_values)
    is_paid = (
        (paid_status and order.status == paid_status)
        or str(order.status).lower() in {"paid", "pago", "confirmed"}
    )

    current_user = getattr(request, "current_user", None)
    can_pay = bool(current_user and order.user_id and current_user.user_id == order.user_id and not is_paid)

    return render(
        request,
        "checkout_success.html",
        {
            "order": order,
            "invoice": invoice,
            "items": items,
            "total": total,
            "can_pay": can_pay,
            "is_paid": is_paid,
        },
    )


def pay_order(request, order_id):
    if request.method != "POST":
        return redirect("/perfil/")

    user = getattr(request, "current_user", None)
    if not user:
        return redirect("/login/?next=/perfil/")

    order = get_object_or_404(Order, order_id=order_id, user_id=user.user_id)

    status_values = _enum_values("order_status")
    paid_status = _resolve_paid_status(status_values)

    if paid_status and order.status != paid_status:
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE public.orders
                SET status = %s,
                    updated_at = now()
                WHERE order_id = %s;
                """,
                [paid_status, order_id],
            )

    return redirect(f"/checkout/sucesso/{order_id}/")


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
                CALL public.update_order(
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
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
            ])

        return redirect('order_list')

    return render(request, 'order/update_order.html', {
        'form': form,
        'order': order
    })


def invoice_list(request):
    invoices = Invoice.objects.select_related("order").all().order_by("-issued_at")
    return render(request, 'order/invoice_list.html', {'invoices': invoices})


def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_related("order"), invoice_id=invoice_id)
    items = []
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT oi.wine_id, oi.quantity, w.name, w.price
                FROM public.order_items oi
                LEFT JOIN public.wines w ON w.wine_id = oi.wine_id
                WHERE oi.order_id = %s
                ORDER BY w.name NULLS LAST;
                """,
                [invoice.order_id],
            )
            items = [
                {
                    "wine_id": row[0],
                    "quantity": row[1],
                    "wine_name": row[2],
                    "unit_price": row[3],
                }
                for row in cur.fetchall()
            ]
    except Exception:
        items = []

    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT oe.event_id, oe.quantity, e.title, e.price_cents, e.is_free
                FROM public.order_event_items oe
                LEFT JOIN public.events e ON e.event_id = oe.event_id
                WHERE oe.order_id = %s
                ORDER BY e.title NULLS LAST;
                """,
                [invoice.order_id],
            )
            for row in cur.fetchall():
                event_price = Decimal("0")
                if row[4]:
                    event_price = Decimal("0")
                elif row[3] is not None:
                    event_price = Decimal(row[3]) / Decimal("100")
                items.append(
                    {
                        "wine_id": row[0],
                        "quantity": row[1],
                        "wine_name": f"Bilhete: {row[2] or row[0]}",
                        "unit_price": event_price,
                    }
                )
    except Exception:
        pass

    pdf_bytes = build_invoice_pdf(invoice, items)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice-{invoice.invoice_number}.pdf"'
    return response
