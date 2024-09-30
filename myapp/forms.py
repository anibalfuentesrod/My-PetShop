from django import forms
from .models import ShippingAddress

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['direccion', 'ciudad', 'estado', 'codigo_postal', 'country']
        widgets = {
            'country': forms.TextInput(attrs={'placeholder': 'Enter your country'}),
        }