from django.db import models


class EventListView(models.Model):
    event_id = models.UUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    is_online = models.BooleanField()
    online_url = models.TextField(null=True, blank=True)

    venue_name = models.CharField(max_length=255, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=32, null=True, blank=True)
    city = models.CharField(max_length=120, null=True, blank=True)
    region = models.CharField(max_length=120, null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64)

    capacity = models.IntegerField(null=True, blank=True)
    price_cents = models.IntegerField(null=True, blank=True)
    currency_code = models.CharField(max_length=3, null=True, blank=True)
    is_free = models.BooleanField()

    status = models.CharField(max_length=20)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    is_published = models.BooleanField()
    is_upcoming = models.BooleanField()
    is_finished = models.BooleanField()
    start_date = models.DateField()
    duration = models.DurationField(null=True, blank=True)

    class Meta:
        db_table = "mv_events_all"
        managed = False

    def __str__(self):
        if self.title:
            return self.title
        return self.slug
