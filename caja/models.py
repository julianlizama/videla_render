from decimal import Decimal

from django.db import models
from django.utils import timezone

from menu.models import Producto


# =========================
# PEDIDOS Y DETALLES
# =========================

class Pedido(models.Model):
    ORIGEN_CHOICES = [
        ("web", "Web"),
        ("local", "Local"),
    ]

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_cocina", "En cocina"),
        ("listo", "Listo"),
        ("entregado", "Entregado"),
        ("cancelado", "Cancelado"),
    ]

    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("tarjeta", "Tarjetas"),
    ]

    TIPO_ENTREGA_CHOICES = [
        ("retiro", "Retiro"),
        ("reparto", "Reparto"),
    ]

    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES)
    canal = models.CharField(
        max_length=20,
        default="mostrador",
        help_text="mostrador, web, delivery, etc.",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente",
    )

    # ==== CAMPOS DEL PAPEL / CLIENTE ====
    nombre_cliente = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMA_PAGO_CHOICES,
        blank=True,
        null=True,
    )
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TIPO_ENTREGA_CHOICES,
        blank=True,
        null=True,
    )

    # Total escrito en la caja (si no hay detalles de productos)
    total_manual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total escrito en caja (opcional).",
    )

    visible_en_cocina = models.BooleanField(
        default=True,
        help_text="Solo los pedidos visibles aparecerán en la pantalla de cocina.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # Nota / detalle general del papel
    nota = models.TextField(blank=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"Pedido #{self.id} ({self.get_origen_display()})"

    @property
    def total(self) -> Decimal:
        """
        Si hay detalles de productos, se usa la suma de subtotales.
        Si no, se usa el total_manual escrito en la caja.
        """
        agg = self.detalles.aggregate(total=models.Sum("subtotal"))
        if agg["total"]:
            return agg["total"]
        return self.total_manual or Decimal("0")


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_caja",
    )
    nombre_producto = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.nombre_producto} (Pedido #{self.pedido_id})"


# =========================
# BOLETAS
# =========================

class Boleta(models.Model):
    """
    Boleta simple ligada 1 a 1 a un Pedido.
    La usamos para reportes y para la vista de boleta.
    """
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name="boleta",
    )
    folio = models.IntegerField(unique=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=30, default="efectivo")
    fecha_emision = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha_emision"]

    def __str__(self) -> str:
        return f"Boleta {self.folio} - {self.monto_total}"

    # ---- Propiedades para que las plantillas funcionen tal cual ----
    @property
    def nombre_cliente(self) -> str:
        return self.pedido.nombre_cliente or ""

    @property
    def total(self) -> Decimal:
        """
        Alias de monto_total para que la plantilla use {{ pedido.total }}.
        """
        return self.monto_total

    @property
    def fecha(self):
        """
        Alias de fecha_emision para que la plantilla use {{ pedido.fecha }}.
        """
        return self.fecha_emision

    # ---- Helper para folio correlativo ----
    @classmethod
    def siguiente_folio(cls) -> int:
        ultimo = cls.objects.order_by("-folio").first()
        if ultimo and ultimo.folio:
            return ultimo.folio + 1
        return 1


# =========================
# INVENTARIO (PRODUCTOS NO PERECIBLES)
# =========================

class ProductoInventario(models.Model):
    nombre = models.CharField(max_length=150)
    sku = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )
    stock_actual = models.IntegerField(default=0)
    precio_costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    def __str__(self) -> str:
        return f"{self.nombre} (stock: {self.stock_actual})"


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
    ]

    producto = models.ForeignKey(
        ProductoInventario,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=100, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Cada movimiento ajusta el stock actual del producto.
        Nota: se asume que los movimientos no se editan luego;
        si editas un movimiento antiguo, ajustará de nuevo el stock.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            if self.tipo == "entrada":
                self.producto.stock_actual += self.cantidad
            else:
                self.producto.stock_actual -= self.cantidad
            self.producto.save()

    def __str__(self) -> str:
        return f"{self.tipo} {self.cantidad} de {self.producto.nombre}"
