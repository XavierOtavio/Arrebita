# Wines/views.py
from urllib.parse import urlencode

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import WineListView, WineType
from Arrebita.reviews import create_review, list_reviews


def winelist(request):
    """
    Lista de vinhos com filtros, ordenação e paginação.
    Lê da VIEW no Postgres (WineListView) e não altera dados.
    """

    # =========================
    # 1) Ler parâmetros GET
    # =========================
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()
    selected_types = request.GET.getlist("type")  # pode ter vários
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")
    rating = request.GET.get("rating")

    # =========================
    # 2) Query base
    # =========================
    wines_qs = WineListView.objects.all()

    # =========================
    # 3) Filtro de pesquisa (nome / casta)
    # =========================
    if q:
        # adapta os campos à tua VIEW: name, grape_variety, etc.
        wines_qs = wines_qs.filter(
            Q(name__icontains=q) |
            Q(region__icontains=q) |
            Q(type_label__icontains=q)
        )

    # =========================
    # 4) Filtro por tipo (checkboxes)
    # =========================
    if selected_types:
        wines_qs = wines_qs.filter(type_id__in=selected_types)

    # =========================
    # 5) Filtro por preço
    # =========================
    if min_price:
        try:
            min_value = float(min_price)
            wines_qs = wines_qs.filter(price__gte=min_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_value = float(max_price)
            wines_qs = wines_qs.filter(price__lte=max_value)
        except ValueError:
            pass

    # =========================
    # 6) Filtro por classificação mínima
    # =========================
    if rating:
        try:
            rating_value = int(rating)
            if 1 <= rating_value <= 5:
                wines_qs = wines_qs.filter(rating__gte=rating_value)
        except ValueError:
            pass

    # =========================
    # 7) Ordenação
    # =========================
    # Chave usada no <select> do HTML
    rating_sort_key = "-rating"  # vai casar com o campo "rating" da VIEW

    allowed_sorts = {
        "name": "name",
        "-name": "-name",
        "price": "price",
        "-price": "-price",
        "-created_at": "-created_at",
        rating_sort_key: rating_sort_key,
    }

    order_by = allowed_sorts.get(sort)
    if order_by:
        wines_qs = wines_qs.order_by(order_by)
    else:
        # ordenação por defeito se não houver 'sort'
        wines_qs = wines_qs.order_by("name")

    # =========================
    # 8) Paginação
    # =========================
    paginator = Paginator(wines_qs, 9)  # 9 vinhos por página, ajusta se quiseres
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    wines_page = page_obj.object_list

    # =========================
    # 9) Querystring para paginação
    # (mantém filtros quando mudas de página)
    # =========================
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    # =========================
    # 10) Dados auxiliares para o template
    # =========================
    wine_types = WineType.objects.all().order_by("name")
    rating_options = [5, 4, 3, 2, 1]

    context = {
        "wines": wines_page,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "querystring": querystring,

        "wine_types": wine_types,
        "selected_types": selected_types,

        "rating_options": rating_options,
        "has_rating_field": True,
        "rating_sort_key": rating_sort_key,
    }

    return render(request, "wine_list.html", context)


def wine_detail(request, wine_id):
    wine = get_object_or_404(WineListView, wine_id=wine_id)

    error = ""
    if request.method == "POST":
        user_name = (request.POST.get("user_name") or "").strip() or "Anonimo"
        rating_raw = (request.POST.get("rating") or "").strip()
        comment = (request.POST.get("comment") or "").strip()

        try:
            rating = int(rating_raw)
        except ValueError:
            rating = 0

        if rating < 1 or rating > 5 or not comment:
            error = "Preenche comentario e rating (1-5)."
        else:
            try:
                create_review(
                    wine_id=wine.wine_id,
                    wine_name=wine.name,
                    user_name=user_name,
                    rating=rating,
                    comment=comment,
                )
                return redirect(request.path)
            except RuntimeError:
                error = "Erro ao ligar ao MongoDB."

    try:
        reviews = list_reviews(wine_id=wine.wine_id, limit=50)
    except RuntimeError:
        reviews = []
        if not error:
            error = "Erro ao ligar ao MongoDB."

    context = {
        "wine": wine,
        "reviews": reviews,
        "error": error,
    }
    return render(request, "wine_detail.html", context)

