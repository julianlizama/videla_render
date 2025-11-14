
from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    class Meta:
        verbose_name_plural = "Categorías"
    def __str__(self): return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name="productos")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    def __str__(self): return self.nombre

class Promocion(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to="promos/", blank=True, null=True)
    activa = models.BooleanField(default=True)
    def __str__(self): return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.nombre} ({self.email})"

class Pedido(models.Model):
    TIPO_ENTREGA = (("retiro","Retiro"),("delivery","Delivery"))
    ESTADO = (("pendiente","Pendiente"),("pagado","Pagado"),("preparando","Preparando"),
              ("listo","Listo"),("entregado","Entregado"),("cancelado","Cancelado"))
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="pedidos")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA, default="retiro")
    direccion = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    preferencia_mp = models.CharField(max_length=200, blank=True)
    def __str__(self): return f"Pedido #{self.id} - {self.cliente.nombre}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self): return f"{self.producto.nombre} x{self.cantidad}"
