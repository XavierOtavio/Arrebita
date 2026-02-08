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

        if request.current_user:
            request.can_backoffice = self._has_permission(
                request.current_user.user_id,
                "backoffice:dashboard",
            )

        if self._is_public_path(path):
            return self.get_response(request)

        if not request.current_user:
            return redirect(f"/login/?next={path}")

        permission = self._permission_for_request(request, path)
        if not self._has_permission(request.current_user.user_id, permission):
            return HttpResponseForbidden("Forbidden: You don't have permission to access this resource." + f" Required permission: {permission}")

        return self.get_response(request)

    @staticmethod
    def _is_public_path(path):
        if path == "/":
            return True

        public_prefixes = (
            "/events",
            "/wines",
            "/comunidade",
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
        try:
            match = resolve(path)
            return match.view_name or match.url_name or path
        except Exception:
            return path

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
