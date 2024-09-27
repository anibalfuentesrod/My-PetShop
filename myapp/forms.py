from django import forms
from .models import ShippingAddress

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['direccion', 'ciudad', 'estado', 'codigo_postal']
    
    # Optionally, set the country field as hidden with a default value
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'] = forms.CharField(initial="Puerto Rico", widget=forms.HiddenInput())