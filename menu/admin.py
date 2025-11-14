
from django.contrib import admin
from .models import Categoria, Producto, Promocion, Cliente, Pedido, DetallePedido

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre","descripcion","activa")
    list_editable = ("activa",)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre","categoria","precio","activo")
    list_filter = ("categoria","activo")
    search_fields = ("nombre",)
    list_editable = ("precio","activo")

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ("nombre","precio","activa")
    list_editable = ("precio","activa")

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre","email","telefono","fecha_registro")
    search_fields = ("email","telefono")

class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id","cliente","tipo_entrega","estado","total","fecha")
    list_filter = ("estado","tipo_entrega")
    inlines = [DetalleInline]
