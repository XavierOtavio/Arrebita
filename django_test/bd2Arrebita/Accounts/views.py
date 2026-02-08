from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import User


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

    return render(request, "profile.html", {"user": user})
