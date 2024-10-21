from django import forms
from .models import ShippingAddress
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['direccion', 'ciudad', 'estado', 'codigo_postal', 'country']
        widgets = {
            'country': forms.TextInput(attrs={'placeholder': 'Enter your country'}),
        }



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