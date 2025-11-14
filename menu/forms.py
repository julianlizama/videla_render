
from django import forms
from .models import Cliente
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre","email","telefono"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class":"form-control","placeholder":"Tu nombre"}),
            "email": forms.EmailInput(attrs={"class":"form-control","placeholder":"correo@dominio.com"}),
            "telefono": forms.TextInput(attrs={"class":"form-control","placeholder":"+56 9 ..."}),
        }
