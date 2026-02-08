from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("comunidade/", views.community, name="community"),

]
