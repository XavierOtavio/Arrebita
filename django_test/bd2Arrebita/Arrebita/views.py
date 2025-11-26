from django.shortcuts import render

def home(request):
    # placeholders que podes depois ligar a BD
    destaques = [
        {"tipo": "Populares", "titulo": "Top da Semana", "img": "img/a2.png", "cta":"Ver vinhos"},
        {"tipo": "Recomendados", "titulo": "Para Ti", "img": "img/a1.png", "cta":"Ver sugestões"},
        {"tipo": "Eventos", "titulo": "Noite Arrebita", "img": "img/a3.png", "cta":"Saber mais"},
    ]
    feed = [
        {"user":"@rita", "avatar":"img/u1.jpg", "texto":"Este Merlot… ui! 🔥", "rating":5, "img":"img/c4.jpg"},
        {"user":"@tiago", "avatar":"img/u2.jpg", "texto":"Tinto sedutor, corpo e final longo.", "rating":4, "img":"img/c10.jpg"},
        {"user":"@tatiana", "avatar":"img/u3.jpg", "texto":"Rosé travesso — leve e divertido 😜", "rating":4, "img":"img/c6.jpg"},
    ]
    return render(request, "home.html", {"destaques": destaques, "feed": feed})



# Create your views here.
