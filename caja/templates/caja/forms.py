from django import forms
from .models import ProductoInventario, MovimientoInventario


class ProductoInventarioForm(forms.ModelForm):
    class Meta:
        model = ProductoInventario
        fields = ["nombre", "sku", "stock_actual", "precio_costo", "precio_venta"]


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ["producto", "tipo", "cantidad", "motivo"]
