from django.shortcuts import render

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



# Create your views here.
