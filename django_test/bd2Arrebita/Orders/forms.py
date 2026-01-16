from django import forms
from django.db import connection

def load_status_choices():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT unnest(enum_range(NULL::public.order_status))::text;
        """)
        return [(row[0], row[0]) for row in cursor.fetchall()]


class OrderForm(forms.Form):
    order_number = forms.CharField(max_length=64, required=False)
    user_id = forms.IntegerField(required=False)
    kind = forms.CharField(max_length=32, required=False)
    status = forms.ChoiceField(choices=[], required=False)
    billing_name = forms.CharField(max_length=200, required=False)
    billing_nif = forms.CharField(max_length=32, required=False)
    billing_address = forms.CharField(widget=forms.Textarea, required=False)
    invoice_url = forms.CharField(required=False)

    def __init__(self, *args, initial_order=None, **kwargs):
        super().__init__(*args, **kwargs)

        # preencher choices do ENUM
        self.fields["status"].choices = load_status_choices()

        if initial_order is not None:
            self.fields['order_number'].initial = initial_order.order_number
            self.fields['user_id'].initial = initial_order.user_id
            self.fields['kind'].initial = initial_order.kind
            self.fields['status'].initial = initial_order.status
            self.fields['billing_name'].initial = initial_order.billing_name
            self.fields['billing_nif'].initial = initial_order.billing_nif
            self.fields['billing_address'].initial = initial_order.billing_address
            self.fields['invoice_url'].initial = initial_order.invoice_url
