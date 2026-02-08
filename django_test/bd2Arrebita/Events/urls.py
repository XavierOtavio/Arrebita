from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.eventlist, name="eventlist"),
    path("<slug:slug>/", views.event_detail, name="event_detail"),
]
