from django import forms


class LoginUserForm(forms.Form):
    uid = forms.CharField(label="uid",
                          widget=forms.NumberInput(attrs={'class': 'form-input'}))
