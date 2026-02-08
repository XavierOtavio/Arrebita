# Wines/views.py
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import WineListView, WineType
from Arrebita.mongo import get_reviews_collection
from Arrebita.reviews import create_review, list_reviews


def winelist(request):
    """
    Lista de vinhos com filtros, ordenacao e paginacao.
    Le da VIEW no Postgres (WineListView) e nao altera dados.
    """

    # =========================
    # 1) Ler parametros GET
    # =========================
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()
    selected_types = request.GET.getlist("type")
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
        wines_qs = wines_qs.filter(
            Q(name__icontains=q)
            | Q(region__icontains=q)
            | Q(type_label__icontains=q)
        )

    # =========================
    # 4) Filtro por tipo (checkboxes)
    # =========================
    if selected_types:
        wines_qs = wines_qs.filter(type_id__in=selected_types)

    # =========================
    # 5) Filtro por preco
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
    # 6) Filtro por classificacao minima (rating vem do Mongo)
    # =========================
    rating_filter_value = None
    if rating:
        try:
            rating_value = int(rating)
            if 1 <= rating_value <= 5:
                rating_filter_value = rating_value
        except ValueError:
            rating_filter_value = None

    # =========================
    # 7) Ordenacao
    # =========================
    rating_sort_key = "-rating"

    allowed_sorts = {
        "name": "name",
        "-name": "-name",
        "price": "price",
        "-price": "-price",
        "-created_at": "-created_at",
    }

    use_rating_sort = sort in {rating_sort_key, "rating"}

    order_by = allowed_sorts.get(sort)
    if order_by:
        wines_qs = wines_qs.order_by(order_by)
    elif not use_rating_sort:
        wines_qs = wines_qs.order_by("name")

    # =========================
    # 8) Paginacao
    # =========================
    def _ratings_map_for(ids):
        if not ids:
            return {}
        try:
            collection = get_reviews_collection()
            str_ids = [str(wid) for wid in ids]
            pipeline = [
                {"$match": {"wine_id": {"$in": str_ids}}},
                {"$group": {"_id": "$wine_id", "avg_rating": {"$avg": "$rating"}}},
            ]
            results = collection.aggregate(pipeline)
            return {row.get("_id"): float(row.get("avg_rating") or 0) for row in results}
        except Exception:
            return {}

    def _attach_ratings(wines, ratings_map):
        for wine in wines:
            avg = ratings_map.get(str(wine.wine_id), 0)
            wine._rating_avg = avg
            try:
                safe = int(round(avg))
            except (TypeError, ValueError):
                safe = 0
            wine._rating_safe = max(0, min(5, safe))

    page_number = request.GET.get("page", 1)

    if use_rating_sort or rating_filter_value is not None:
        wines_list = list(wines_qs)
        ratings_map = _ratings_map_for([wine.wine_id for wine in wines_list])
        _attach_ratings(wines_list, ratings_map)

        if rating_filter_value is not None:
            wines_list = [
                wine for wine in wines_list
                if getattr(wine, "_rating_avg", 0) >= rating_filter_value
            ]

        if use_rating_sort:
            reverse = sort.startswith("-")
            wines_list.sort(
                key=lambda wine: (getattr(wine, "_rating_avg", 0), wine.name or ""),
                reverse=reverse,
            )

        paginator = Paginator(wines_list, 9)
        page_obj = paginator.get_page(page_number)
        wines_page = page_obj.object_list
    else:
        paginator = Paginator(wines_qs, 9)
        page_obj = paginator.get_page(page_number)
        wines_page = page_obj.object_list

        ratings_map = _ratings_map_for([wine.wine_id for wine in wines_page])
        _attach_ratings(wines_page, ratings_map)

    # =========================
    # 9) Querystring para paginacao
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
    rating_avg = 0
    rating_count = 0
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

    if reviews:
        rating_count = len(reviews)
        try:
            rating_avg = sum((r.get("rating", 0) or 0) for r in reviews) / rating_count
        except (TypeError, ZeroDivisionError):
            rating_avg = 0

    try:
        collection = get_reviews_collection()
        agg = list(collection.aggregate([
            {"$match": {"wine_id": str(wine.wine_id)}},
            {"$group": {"_id": "$wine_id", "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}},
        ]))
        if agg:
            rating_avg = float(agg[0].get("avg_rating") or 0)
            rating_count = int(agg[0].get("count") or 0)
    except Exception:
        pass

    try:
        rating_safe = int(round(rating_avg))
    except (TypeError, ValueError):
        rating_safe = 0
    rating_safe = max(0, min(5, rating_safe))

    context = {
        "wine": wine,
        "reviews": reviews,
        "error": error,
        "rating_avg": rating_avg,
        "rating_count": rating_count,
        "rating_safe": rating_safe,
    }
    return render(request, "wine_detail.html", context)
