from django.contrib import admin
from .models import (
    Pedido,
    DetallePedido,
    Boleta,
    ProductoInventario,
    MovimientoInventario,
)

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "origen", "canal", "estado", "creado_en", "total")
    list_filter = ("origen", "estado", "canal", "creado_en")
    search_fields = ("nombre_cliente",)
    inlines = [DetallePedidoInline]

@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    list_display = ("folio", "pedido", "monto_total", "metodo_pago", "fecha_emision")
    list_filter = ("metodo_pago", "fecha_emision")

@admin.register(ProductoInventario)
class ProductoInventarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sku", "stock_actual", "precio_costo", "precio_venta")
    search_fields = ("nombre", "sku")

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "producto", "tipo", "cantidad", "motivo")
    list_filter = ("tipo", "fecha")
