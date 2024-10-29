from django import forms
from django.forms import HiddenInput


class CostForm(forms.Form):
    class Meta:
        widgets = {'any_field': HiddenInput(), }
