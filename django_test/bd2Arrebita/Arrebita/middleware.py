from django.db import connection
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import resolve

from Accounts.models import User


class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or "/"

        request.current_user = self._get_current_user(request)
        request.can_backoffice = False
        request.cart_count = self._cart_count(request)

        if request.current_user:
            request.can_backoffice = any(
                self._has_permission(request.current_user.user_id, perm)
                for perm in ("backoffice.dashboard", "backoffice:dashboard", "dashboard")
            )

        if self._is_public_path(path):
            return self.get_response(request)

        if not request.current_user:
            return redirect(f"/login/?next={path}")

        permissions = self._permission_for_request(request, path)
        allowed = any(
            self._has_permission(request.current_user.user_id, perm)
            for perm in permissions
            if perm
        )
        if not allowed:
            required = permissions[0] if permissions else path
            return HttpResponseForbidden(
                "Forbidden: You don't have permission to access this resource."
                + f" Required permission: {required}"
            )

        return self.get_response(request)

    @staticmethod
    def _is_public_path(path):
        if path == "/":
            return True

        public_prefixes = (
            "/events",
            "/wines",
            "/comunidade",
            "/cart",
            "/checkout",
            "/login",
            "/registo",
            "/logout",
            "/accounts/login",
            "/accounts/registo",
            "/accounts/logout",
            "/Static",
            "/static",
            "/admin",
            "/favicon.ico",
        )
        return any(path.startswith(prefix) for prefix in public_prefixes)

    @staticmethod
    def _permission_for_request(request, path):
        if path in {"/backoffice", "/backoffice/"}:
            return ["backoffice.dashboard"]

        if path in {"/perfil", "/perfil/"}:
            return ["accounts.profile"]

        if path.startswith("/orders/invoices"):
            return ["orders.invoices", "orders.my_invoices"]

        try:
            match = resolve(path)
            permissions = []

            module = match.app_name or match.namespace
            url_name = match.url_name
            view_name = match.view_name

            if not url_name and view_name and ":" in view_name:
                url_name = view_name.split(":")[-1]

            if not module and view_name and ":" in view_name:
                module = view_name.split(":")[0]

            if not module:
                module = AccessControlMiddleware._module_from_path(path)

            if module and url_name:
                functionality = AccessControlMiddleware._normalize_permission(
                    module, url_name
                )
                permissions.append(f"{module}.{functionality}")

                if module == "orders" and functionality == "invoices":
                    permissions.append("orders.my_invoices")

            if view_name and ":" in view_name:
                permissions.append(view_name.replace(":", "."))

            if view_name and view_name not in permissions:
                permissions.append(view_name)

            if url_name and url_name not in permissions:
                permissions.append(url_name)

            if not permissions:
                permissions.append(path)
            return permissions
        except Exception:
            if path.startswith("/backoffice"):
                return ["backoffice.dashboard"]
            return [path]

    @staticmethod
    def _normalize_permission(module, url_name):
        if module != "backoffice":
            mappings = {
                "wine": {
                    "winelist": "list",
                    "wine_detail": "detail",
                },
                "events": {
                    "eventlist": "list",
                },
                "orders": {
                    "order_list": "list",
                    "update_order": "update",
                    "invoice_list": "invoices",
                    "invoice_pdf": "invoices",
                },
                "accounts": {
                    "profile": "profile",
                    "login": "login",
                    "register": "register",
                    "logout": "logout",
                },
                "statistics": {
                    "index": "dashboard",
                },
                "community": {
                    "community": "list",
                },
            }

            return mappings.get(module, {}).get(url_name, url_name)

        name = url_name
        if name.startswith("backoffice_"):
            name = name[len("backoffice_"):]

        if name == "dashboard":
            return "dashboard"
        if name.startswith("wine"):
            return "wines"
        if name.startswith("event"):
            return "events"
        if name.startswith("order") or name.startswith("invoice"):
            return "orders"
        if name.startswith("user"):
            return "users"

        return name

    @staticmethod
    def _module_from_path(path):
        if path.startswith("/wines"):
            return "wine"
        if path.startswith("/events"):
            return "events"
        if path.startswith("/orders"):
            return "orders"
        if path.startswith("/statistics"):
            return "statistics"
        if path.startswith("/comunidade"):
            return "community"
        if path.startswith("/perfil") or path.startswith("/login") or path.startswith("/registo") or path.startswith("/logout"):
            return "accounts"
        if path.startswith("/backoffice"):
            return "backoffice"
        return None

    @staticmethod
    def _has_permission(user_id, permission):
        with connection.cursor() as cur:
            cur.execute("SELECT fn_user_has_permission(%s, %s);", [user_id, permission])
            row = cur.fetchone()
            return bool(row and row[0])

    @staticmethod
    def _get_current_user(request):
        user_id = request.session.get("user_id")
        if not user_id:
            return None
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            request.session.flush()
            return None

    @staticmethod
    def _cart_count(request):
        cart = request.session.get("cart", {})
        if not isinstance(cart, dict):
            return 0
        total = 0
        if "wines" in cart or "events" in cart:
            buckets = []
            wines = cart.get("wines")
            events = cart.get("events")
            if isinstance(wines, dict):
                buckets.append(wines)
            if isinstance(events, dict):
                buckets.append(events)
            for bucket in buckets:
                for qty in bucket.values():
                    try:
                        total += int(qty)
                    except (TypeError, ValueError):
                        continue
            return total

        for qty in cart.values():
            try:
                total += int(qty)
            except (TypeError, ValueError):
                continue
        return total
