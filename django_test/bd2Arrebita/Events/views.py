from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from .models import EventListView

STATUS_LABELS = {
    "draft": "Rascunho",
    "published": "Publicado",
    "cancelled": "Cancelado",
    "archived": "Arquivado",
}


def _format_price(event):
    if event.is_free:
        return "Gratuito"
    if event.price_cents is None:
        return "Preco a definir"
    currency = (event.currency_code or "EUR").strip() or "EUR"
    return f"{currency} {event.price_cents / 100:.2f}"


def _format_location(event):
    if event.is_online:
        return "Online"
    parts = []
    if event.venue_name:
        parts.append(event.venue_name)
    city_parts = [event.city, event.region, event.country_code]
    city_line = ", ".join([part for part in city_parts if part])
    if city_line:
        parts.append(city_line)
    return " - ".join(parts)


def _format_summary(event, limit=180):
    text = (event.summary or event.description or "").strip()
    if not text:
        return ""
    if len(text) > limit:
        return f"{text[:limit - 3].rstrip()}..."
    return text


def _format_duration(event):
    if not event.duration:
        return ""
    total_minutes = int(event.duration.total_seconds() // 60)
    if total_minutes <= 0:
        return ""
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def eventlist(request):
    mode = request.GET.get("mode", "").strip()
    price = request.GET.get("price", "").strip()
    status = request.GET.get("status", "").strip()
    timing = request.GET.get("timing", "").strip()
    sort = request.GET.get("sort", "").strip()

    events_qs = EventListView.objects.all()

    if mode == "online":
        events_qs = events_qs.filter(is_online=True)
    elif mode == "onsite":
        events_qs = events_qs.filter(is_online=False)

    if price == "free":
        events_qs = events_qs.filter(is_free=True)
    elif price == "paid":
        events_qs = events_qs.filter(is_free=False)

    if status:
        events_qs = events_qs.filter(status=status)

    if timing == "upcoming":
        events_qs = events_qs.filter(is_upcoming=True)
    elif timing == "finished":
        events_qs = events_qs.filter(is_finished=True)
    elif timing == "ongoing":
        events_qs = events_qs.filter(is_upcoming=False, is_finished=False)

    allowed_sorts = {
        "starts_at": "starts_at",
        "-starts_at": "-starts_at",
        "price": "price_cents",
        "-price": "-price_cents",
    }
    events_qs = events_qs.order_by(allowed_sorts.get(sort, "starts_at"))

    paginator = Paginator(events_qs, 6)
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    events_page = list(page_obj.object_list)

    for event in events_page:
        title = (event.title or "").strip()
        slug = (event.slug or "").strip()
        if title:
            event.display_title = title
        elif slug:
            event.display_title = slug.replace("-", " ").title()
        else:
            event.display_title = f"Evento {event.event_id}"

        event.format_label = "Online" if event.is_online else "Presencial"
        event.status_label = STATUS_LABELS.get(event.status, event.status or "")
        event.price_display = _format_price(event)
        event.location_display = _format_location(event)
        event.summary_display = _format_summary(event)
        event.duration_display = _format_duration(event)
        if event.is_finished:
            event.timing_label = "Terminado"
        elif event.is_upcoming:
            event.timing_label = "Proximo"
        else:
            event.timing_label = "Em curso"

        if event.is_online and event.online_url:
            event.cta_url = event.online_url
        else:
            event.cta_url = "#"
        event.cta_label = "Comprar bilhete" if not event.is_free else "Inscrever"

    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    context = {
        "events": events_page,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "querystring": querystring,
        "mode": mode,
        "price": price,
        "status": status,
        "timing": timing,
        "sort": sort,
    }

    return render(request, "events-list.html", context)
