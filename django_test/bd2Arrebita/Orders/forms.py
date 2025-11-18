from django import forms
from django.db import connection

def load_status_choices():
    with connection.cursor() as cursor:
        cursor.execute("SELECT unnest(enum_range(NULL::public.order_status))::text")
        rows = cursor.fetchall()
    return [(r[0], r[0]) for r in rows]

class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(choices=[], required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = load_status_choices()

