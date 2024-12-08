from django import forms
from django.forms import HiddenInput


class CostForm(forms.Form):
    class Meta:
        widgets = {'any_field': HiddenInput(), }


class PremiumChatForm(forms.Form):
    chatid = forms.IntegerField(min_value=1, max_value=100000000)

    class Meta:
        widgets = {'any_field': HiddenInput(), }
