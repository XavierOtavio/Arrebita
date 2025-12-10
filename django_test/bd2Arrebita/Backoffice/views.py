from django.shortcuts import render
# no futuro poderás importar modelos ou chamar procedures aqui
# from Wines.models import WineListView
from django.db import connection
from django.shortcuts import render, redirect
from django.urls import reverse
import uuid



def dashboard(request):
    """
    Página inicial do backoffice.
    Por agora não mexe em base de dados para garantir que nada parte.
    """
    return render(request, "dashboard.html")


# EXEMPLO FUTURO: listar vinhos no backoffice (ainda não obrigatório)
# def wine_list(request):
#     wines = WineListView.objects.all().order_by("name")
#     return render(request, "backoffice/wine_list.html", {"wines": wines})



def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [
        dict(zip(cols, row))
        for row in cursor.fetchall()
    ]


def backoffice_wines(request):
    # 1) Carregar tipos de vinho via função get_wine_types()
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM get_wine_types();")
        wine_types = dictfetchall(cur)

    # 2) Filtros vindos da querystring
    q = request.GET.get("q") or ""
    type_id = request.GET.get("type") or None
    region = request.GET.get("region") or ""
    only_on_promo = bool(request.GET.get("only_on_promo"))

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
              promo_pct_off,
              promo_price,
              has_active_promo
          FROM public.vw_wine_list
          WHERE 1 = 1 \
          """
    params = []

    if q:
        sql += " AND (name ILIKE %s OR sku ILIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    if type_id:
        sql += " AND type_id = %s"
        params.append(uuid.UUID(type_id))

    if region:
        sql += " AND region ILIKE %s"
        params.append(f"%{region}%")

    if only_on_promo:
        sql += " AND has_active_promo = TRUE"

    with connection.cursor() as cur:
        cur.execute(sql, params)
        wines = dictfetchall(cur)

    context = {
        "wines": wines,
        "wine_types": wine_types,
    }
    return render(request, "vinhos_catalogo.html", context)


def backoffice_wine_create(request):
    if request.method != "POST":
        return redirect(reverse("backoffice_wines"))

    data = request.POST

    with connection.cursor() as cur:
        cur.callproc(
            "create_wine",
            [
                data.get("sku"),
                data.get("name"),
                uuid.UUID(data.get("type_id")),
                data.get("region") or None,
                int(data.get("vintage_year") or 0) or None,
                float(data.get("price")),
                int(data.get("stock_qty")),
                data.get("tasting_notes") or None,
                float(data.get("alcohol_content") or 0) or None,
                float(data.get("serving_temperature") or 0) or None,
                float(data.get("bottle_capacity") or 0) or None,
                data.get("pairing") or None,
                data.get("winemaker") or None,
                ],
        )

    return redirect(reverse("backoffice_wines"))


def backoffice_wine_delete(request, wine_id):
    if request.method != "POST":
        return redirect(reverse("backoffice_wines"))

    with connection.cursor() as cur:
        cur.callproc("delete_wine", [uuid.UUID(wine_id)])

    return redirect(reverse("backoffice_wines"))
