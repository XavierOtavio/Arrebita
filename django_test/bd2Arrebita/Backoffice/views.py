from django.db import connection
from django.shortcuts import render, redirect
from django.urls import reverse
import uuid


def dashboard(request):
    return render(request, "dashboard.html")


def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def backoffice_wines(request):
    """
    Lista de vinhos do backoffice, baseada na view vw_wine_list.
    A view deve expor, pelo menos:
      - wine_id, sku, name, type_id, type_label
      - region (nome da região)
      - vintage_year, price, stock_qty
      - tasting_notes, alcohol_content, serving_temperature,
        bottle_capacity, pairing, winemaker
      - promo_pct_off, promo_price, has_active_promo
    """

    # 1) Tipos de vinho
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM get_wine_types();")
        wine_types = dictfetchall(cur)

    # 2) Regiões normalizadas
    with connection.cursor() as cur:
        cur.execute(
            "SELECT region_id, name FROM public.regions ORDER BY name;"
        )
        regions = dictfetchall(cur)

    # 3) Filtros da querystring
    q = request.GET.get("q") or ""
    type_id = request.GET.get("type") or None
    region = request.GET.get("region") or ""
    only_on_promo = bool(request.GET.get("only_on_promo"))

    # 4) Query base
    sql = """
          SELECT
              wine_id,
              sku,
              name,
              type_id,
              type_label,
              region,
              vintage_year,
              price,
              stock_qty,
              tasting_notes,
              alcohol_content,
              serving_temperature,
              bottle_capacity,
              pairing,
              winemaker,
              promo_pct_off,
              promo_price,
              has_active_promo
          FROM public.vw_wine_list
          WHERE 1 = 1
          """
    params = []

    # 5) Filtro de pesquisa geral (nome / SKU)
    if q:
        sql += " AND (name ILIKE %s OR sku ILIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    # 6) Filtro por tipo de vinho
    if type_id:
        sql += " AND type_id = %s"
        params.append(uuid.UUID(type_id))

    # 7) Filtro por nome da região (exposto pela view)
    if region:
        sql += " AND region ILIKE %s"
        params.append(f"%{region}%")

    # 8) Filtro: apenas vinhos com promoção ativa
    if only_on_promo:
        sql += " AND has_active_promo = TRUE"

    # 9) Execução da query de vinhos
    with connection.cursor() as cur:
        cur.execute(sql, params)
        wines = dictfetchall(cur)

    # 10) Carregar imagens de vinhos e associar a cada vinho
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT image_id, wine_id, image_url, image_type, created_at
            FROM public.wine_images
            ORDER BY created_at DESC;
            """
        )
        images = dictfetchall(cur)

    images_by_wine = {}
    for img in images:
        wkey = str(img["wine_id"])
        images_by_wine.setdefault(wkey, []).append(img)

    for w in wines:
        w["images"] = images_by_wine.get(str(w["wine_id"]), [])

    context = {
        "wines": wines,
        "wine_types": wine_types,
        "regions": regions,
    }
    return render(request, "vinhos_catalogo.html", context)


def backoffice_wine_create(request):
    if request.method != "POST":
        return redirect(reverse("backoffice:backoffice_wines"))

    data = request.POST

    def to_int(value):
        value = value or None
        return int(value) if value is not None and value != "" else None

    def to_float(value):
        value = value or None
        return float(value) if value is not None and value != "" else None

    region_id_str = data.get("region_id")
    region_id = uuid.UUID(region_id_str) if region_id_str else None

    params = [
        data.get("sku"),
        data.get("name"),
        uuid.UUID(data.get("type_id")),
        region_id,                              # region_id (UUID)
        to_int(data.get("vintage_year")),
        to_float(data.get("price")),
        to_int(data.get("stock_qty")),
        data.get("tasting_notes") or None,
        to_float(data.get("alcohol_content")),
        to_float(data.get("serving_temperature")),
        to_float(data.get("bottle_capacity")),
        data.get("pairing") or None,
        data.get("winemaker") or None,
        ]

    with connection.cursor() as cur:
        cur.execute(
            """
            CALL public.create_wine(
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            );
            """,
            params,
        )

    return redirect(reverse("backoffice:backoffice_wines"))


def backoffice_wine_update(request, wine_id):
    """
    Atualiza um vinho existente, chamado a partir do modal Editar.
    """
    if request.method != "POST":
        return redirect(reverse("backoffice:backoffice_wines"))

    data = request.POST

    def to_int(value):
        value = value or None
        return int(value) if value is not None and value != "" else None

    def to_float(value):
        value = value or None
        return float(value) if value is not None and value != "" else None

    region_id_str = data.get("region_id")
    region_id = uuid.UUID(region_id_str) if region_id_str else None

    params = [
        uuid.UUID(wine_id),
        data.get("sku"),
        data.get("name"),
        uuid.UUID(data.get("type_id")),
        region_id,                              # region_id (UUID)
        to_int(data.get("vintage_year")),
        to_float(data.get("price")),
        to_int(data.get("stock_qty")),
        data.get("tasting_notes") or None,
        to_float(data.get("alcohol_content")),
        to_float(data.get("serving_temperature")),
        to_float(data.get("bottle_capacity")),
        data.get("pairing") or None,
        data.get("winemaker") or None,
        ]

    with connection.cursor() as cur:
        cur.execute(
            """
            CALL public.update_wine(
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            );
            """,
            params,
        )

    return redirect(reverse("backoffice:backoffice_wines"))


def backoffice_wine_delete(request, wine_id):
    if request.method != "POST":
        return redirect(reverse("backoffice:backoffice_wines"))

    with connection.cursor() as cur:
        cur.execute(
            "CALL public.delete_wine(%s);",
            [uuid.UUID(wine_id)],
        )

    return redirect(reverse("backoffice:backoffice_wines"))


def backoffice_wine_image_create(request, wine_id):
    """
    Cria uma imagem para um vinho específico.
    """
    if request.method != "POST":
        return redirect(reverse("backoffice:backoffice_wines"))

    data = request.POST
    image_url = data.get("image_url") or ""
    image_type = data.get("image_type") or "catalog"

    if not image_url.strip():
        # Não vale a pena criar entradas vazias
        return redirect(reverse("backoffice:backoffice_wines"))

    with connection.cursor() as cur:
        cur.execute(
            """
            CALL public.create_wine_image(%s, %s, %s);
            """,
            [uuid.UUID(wine_id), image_url, image_type],
        )

    return redirect(reverse("backoffice:backoffice_wines"))


def backoffice_wine_image_delete(request, wine_id, image_id):
    """
    Apaga uma imagem de vinho.
    """
    if request.method != "POST":
        return redirect(reverse("backoffice:backoffice_wines"))

    with connection.cursor() as cur:
        cur.execute(
            "CALL public.delete_wine_image(%s);",
            [uuid.UUID(image_id)],
        )

    return redirect(reverse("backoffice:backoffice_wines"))
