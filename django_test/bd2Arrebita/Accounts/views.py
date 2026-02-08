from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import User
from Orders.models import Order, Invoice


def _now_naive():
    now = timezone.now()
    if timezone.is_aware(now):
        now = timezone.localtime(now).replace(tzinfo=None)
    return now


def _default_role():
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT role FROM public.users ORDER BY user_id LIMIT 1;")
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass

    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'user_role'::regtype ORDER BY enumsortorder LIMIT 1;"
            )
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass

    return "customer"


def _session_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return None


def login_view(request):
    error = ""
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = (request.POST.get("password") or "").strip()

        user = User.objects.filter(email=email, password_hash=password).first()
        if user:
            request.session["user_id"] = user.user_id
            request.session["user_email"] = user.email
            next_url = request.GET.get("next") or "/perfil/"
            return redirect(next_url)

        error = "Credenciais invalidas."

    return render(request, "login.html", {"error": error})


def register_view(request):
    error = ""
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = (request.POST.get("password") or "").strip()

        if not full_name or not email or not password:
            error = "Preenche todos os campos."
        elif User.objects.filter(email=email).exists():
            error = "Email ja registado."
        else:
            role = _default_role()
            user = User.objects.create(
                email=email,
                password_hash=password,
                full_name=full_name,
                role=role,
                created_at=_now_naive(),
            )
            request.session["user_id"] = user.user_id
            request.session["user_email"] = user.email
            return redirect("/perfil/")

    return render(request, "register.html", {"error": error})


def logout_view(request):
    request.session.flush()
    return redirect("/login/")


def profile(request):
    user = _session_user(request)
    if not user:
        return redirect("/login/?next=/perfil/")

    orders = list(Order.objects.filter(user_id=user.user_id).order_by("-created_at"))
    invoices = list(
        Invoice.objects.filter(order__in=orders)
        .select_related("order")
        .order_by("-issued_at")
    )

    invoice_map = {invoice.order_id: invoice for invoice in invoices}
    for order in orders:
        order.invoice = invoice_map.get(order.order_id)

    stats = {
        "orders_total": 0,
        "invoices_total": 0,
        "items_total": 0,
        "spend_total": 0,
        "last_order_at": None,
        "last_invoice_at": None,
    }
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*), MAX(created_at)
                FROM public.orders
                WHERE user_id = %s;
                """,
                [user.user_id],
            )
            row = cur.fetchone()
            if row:
                stats["orders_total"] = row[0] or 0
                stats["last_order_at"] = row[1]

            cur.execute(
                """
                SELECT COUNT(*), MAX(issued_at)
                FROM public.invoices i
                JOIN public.orders o ON o.order_id = i.order_id
                WHERE o.user_id = %s;
                """,
                [user.user_id],
            )
            row = cur.fetchone()
            if row:
                stats["invoices_total"] = row[0] or 0
                stats["last_invoice_at"] = row[1]

            cur.execute(
                """
                SELECT
                    COALESCE(SUM(oi.quantity), 0) AS items_total,
                    COALESCE(SUM(oi.quantity * w.price), 0) AS spend_total
                FROM public.order_items oi
                JOIN public.orders o ON o.order_id = oi.order_id
                LEFT JOIN public.vw_wine_list w ON w.wine_id = oi.wine_id
                WHERE o.user_id = %s;
                """,
                [user.user_id],
            )
            row = cur.fetchone()
            if row:
                stats["items_total"] = row[0] or 0
                stats["spend_total"] = row[1] or 0
    except Exception:
        pass

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password_hash = (request.POST.get("password_hash") or "").strip()

        if full_name and email:
            updates = {"full_name": full_name, "email": email}
            if password_hash:
                updates["password_hash"] = password_hash
            User.objects.filter(user_id=user.user_id).update(**updates)

        return redirect("/perfil/")

    return render(
        request,
        "profile.html",
        {
            "user": user,
            "orders": orders,
            "invoices": invoices,
            "stats": stats,
        },
    )
