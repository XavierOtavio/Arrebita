from django.shortcuts import render

def home(request):
    # placeholders que podes depois ligar a BD
    destaques = [
        {"tipo": "Populares", "titulo": "Top da Semana", "img": "img/card1.jpg", "cta":"Ver vinhos"},
        {"tipo": "Recomendados", "titulo": "Para Ti", "img": "img/card2.jpg", "cta":"Ver sugestões"},
        {"tipo": "Eventos", "titulo": "Noite Arrebita", "img": "img/card3.jpg", "cta":"Saber mais"},
    ]
    feed = [
        {"user":"@rita", "avatar":"img/u1.jpg", "texto":"Este Merlot… ui! 🔥", "rating":5, "img":"img/p1.jpg"},
        {"user":"@tiago", "avatar":"img/u2.jpg", "texto":"Tinto sedutor, corpo e final longo.", "rating":4, "img":"img/p2.jpg"},
        {"user":"@tatiana", "avatar":"img/u3.jpg", "texto":"Rosé travesso — leve e divertido 😜", "rating":4, "img":"img/p3.jpg"},
    ]
    return render(request, "home.html", {"destaques": destaques, "feed": feed})



# Create your views here.
