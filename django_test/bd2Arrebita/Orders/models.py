from django.db import models

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=64, unique=True)
    user_id = models.IntegerField(blank=True, null=True)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=32)  # ENUM no PostgreSQL
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    billing_name = models.CharField(max_length=200, blank=True, null=True)
    billing_nif = models.CharField(max_length=32, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.DO_NOTHING,
        db_column='order_id',
        related_name='invoices'
    )
    issued_at = models.DateTimeField()
    invoice_number = models.CharField(max_length=64, unique=True)

    class Meta:
        managed = False
        db_table = 'invoices'


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items',
    )
    wine_id = models.UUIDField()
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'order_items'


class OrderEventItem(models.Model):
    order_event_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='event_items',
    )
    event_id = models.UUIDField()
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'order_event_items'


class VwOrderSummary(models.Model):
    order_id = models.IntegerField(primary_key=True)
    order_number = models.CharField(max_length=64)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    billing_name = models.CharField(max_length=200)
    billing_nif = models.CharField(max_length=32)
    billing_address = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_email = models.CharField(max_length=255)
    customer_role = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'vw_order_summary'


class VwInvoiceSummary(models.Model):
    invoice_id = models.IntegerField(primary_key=True)
    invoice_number = models.CharField(max_length=64)
    issued_at = models.DateTimeField()
    order_id = models.IntegerField()
    order_number = models.CharField(max_length=64)
    billing_name = models.CharField(max_length=200)
    billing_nif = models.CharField(max_length=32)
    billing_address = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_email = models.CharField(max_length=255)
    customer_role = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'vw_invoice_summary'
