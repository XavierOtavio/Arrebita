from django.db import models


class WineType(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "wine_types"
        managed = False

    def __str__(self):
        return self.name



class WineListView(models.Model):
    wine_id = models.UUIDField(primary_key=True)
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    type_id = models.UUIDField(null=True, blank=True)
    type_label = models.CharField(max_length=100, null=True, blank=True)

    region = models.CharField(max_length=100, null=True, blank=True)
    vintage_year = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_qty = models.IntegerField(null=True, blank=True)

    tasting_notes = models.TextField(null=True, blank=True)
    alcohol_content = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    serving_temperature = models.IntegerField(null=True, blank=True)
    bottle_capacity = models.IntegerField(null=True, blank=True)
    pairing = models.TextField(null=True, blank=True)
    winemaker = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    primary_image_url = models.CharField(max_length=500, null=True, blank=True)
    primary_image_type = models.CharField(max_length=50, null=True, blank=True)

    grape_varieties = models.CharField(max_length=500, null=True, blank=True)

    promo_pct_off = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promo_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    has_active_promo = models.BooleanField()

    class Meta:
        db_table = "vw_wine_list"
        managed = False

    def __str__(self):
        return self.name

    @property
    def rating_safe(self):
        """
        Placeholder temporário: rating virá do MongoDB.
        Por agora devolve sempre 0 para não rebentar o template.
        """
        return 0
