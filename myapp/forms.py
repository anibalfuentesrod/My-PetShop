from django import forms
from .models import ShippingAddress
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['direccion', 'ciudad', 'estado', 'codigo_postal', 'country']
        widgets = {
            'direccion': forms.TextInput(attrs={'placeholder': 'e.g., Carretera 123'}),
            'ciudad': forms.TextInput(attrs={'placeholder': 'e.g., San Juan'}),
            'estado': forms.TextInput(attrs={'placeholder': 'e.g., Puerto Rico'}),
            'codigo_postal': forms.TextInput(attrs={'placeholder': 'e.g., 00685'}),
            'country': forms.TextInput(attrs={'placeholder': 'e.g., US', 'style': 'text-transform: uppercase;'}),
        }
        help_texts = {
            'direccion': 'Enter your street address.',
            'ciudad': 'Enter your city.',
            'estado': 'Enter your state or region.',
            'codigo_postal': 'Enter your postal code.',
            'country': 'Enter your country code in uppercase (e.g., US).',
        }

    def clean_country(self):
        country = self.cleaned_data.get('country')
        return country.upper()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user