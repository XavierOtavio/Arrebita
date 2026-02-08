from django.shortcuts import render, redirect

from Wines.models import WineListView
from .reviews import create_review, list_reviews

def home(request):
    # placeholders que podes depois ligar a BD
    destaques = [
        {"tipo": "Populares", "titulo": "Top da Semana", "img": "img/a2.png", "cta":"Ver vinhos"},
        {"tipo": "Recomendados", "titulo": "Para Ti", "img": "img/a1.png", "cta":"Ver sugestões"},
        {"tipo": "Eventos", "titulo": "Noite Arrebita", "img": "img/a3.png", "cta":"Saber mais"},
    ]
    feed = [
        {"user":"@colaco", "avatar":"img/u4.jpg", "texto":"Este Merlot… ui! 🔥", "rating":5, "img":"img/c5.jpg"},
        {"user":"@joao", "avatar":"img/u6.jpg", "texto":"Tinto sedutor, corpo e final longo.", "rating":4, "img":"img/c10.jpg"},
        {"user":"@pires", "avatar":"img/u2.jpg", "texto":"Rosé travesso — leve e divertido 😜", "rating":4, "img":"img/c7.jpg"},
    ]
    return render(request, "home.html", {"destaques": destaques, "feed": feed})


def community(request):
    error = ""
    wines = list(WineListView.objects.all().order_by("name")[:200])

    if request.method == "POST":
        wine_id_raw = (request.POST.get("wine_id") or "").strip()
        user_name = (request.POST.get("user_name") or "").strip() or "Anonimo"
        rating_raw = (request.POST.get("rating") or "").strip()
        comment = (request.POST.get("comment") or "").strip()

        wine_id = wine_id_raw or None

        try:
            rating = int(rating_raw)
        except ValueError:
            rating = 0

        wine = WineListView.objects.filter(wine_id=wine_id).first() if wine_id else None

        if not wine or rating < 1 or rating > 5 or not comment:
            error = "Preenche vinho, comentario e rating (1-5)."
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
        reviews = list_reviews(limit=60)
    except RuntimeError:
        reviews = []
        if not error:
            error = "Erro ao ligar ao MongoDB."

    context = {
        "wines": wines,
        "reviews": reviews,
        "error": error,
    }
    return render(request, "community.html", context)


# Create your views here.
