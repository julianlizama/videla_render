# menu/views.py
from decimal import Decimal
import urllib.parse

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Prefetch

from .models import Producto, Promocion, Categoria
from caja.models import Pedido, DetallePedido, Boleta


# =========================
# Helpers de carrito (session)
# =========================
def _get_cart(request: HttpRequest) -> dict:
    """
    Obtiene el carrito desde la sesión.
    Siempre devuelve un dict.
    """
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    return cart


def _save_cart(request: HttpRequest, cart: dict) -> None:
    """
    Guarda el carrito en la sesión.
    """
    request.session["cart"] = cart
    request.session.modified = True


def _normalize_cart_dict(cart: dict) -> dict:
    """
    Convierte entradas antiguas tipo {"12": 2} a
    {"12": {"nombre":..., "precio":..., "cantidad":2}}
    usando la BD para completar nombre y precio de PRODUCTOS.
    Las promos ya las guardamos siempre con nombre/precio, así que no se tocan.
    """
    if not cart:
        return {}

    normalized: dict = {}
    ids_a_buscar = []

    for pid, data in cart.items():
        # Formato correcto (dict con posible info)
        if isinstance(data, dict):
            try:
                cantidad = int(data.get("cantidad", 1))
            except Exception:
                cantidad = 1

            nombre = data.get("nombre")
            precio = data.get("precio")

            if nombre and (precio is not None):
                # Ya está completo
                normalized[pid] = {
                    "nombre": str(nombre),
                    "precio": float(precio),
                    "cantidad": cantidad,
                }
            else:
                # Hay que completar desde la BD de productos
                try:
                    ids_a_buscar.append(int(pid))
                except Exception:
                    continue
                normalized[pid] = {"cantidad": cantidad}

        # Formato antiguo (int -> solo cantidad)
        elif isinstance(data, int):
            try:
                ids_a_buscar.append(int(pid))
            except Exception:
                continue
            normalized[pid] = {"cantidad": int(data)}

        # Cualquier otra cosa, omitir
        else:
            continue

    # Completar datos de productos desde la BD
    if ids_a_buscar:
        productos = Producto.objects.filter(id__in=ids_a_buscar).only("id", "nombre", "precio")
        prod_map = {p.id: p for p in productos}
        for pid in list(normalized.keys()):
            # Si ya tiene nombre y precio, no tocar
            if "nombre" in normalized[pid] and "precio" in normalized[pid]:
                continue

            try:
                pid_int = int(pid)
            except Exception:
                normalized.pop(pid, None)
                continue

            p = prod_map.get(pid_int)
            if p:
                normalized[pid].update({
                    "nombre": p.nombre,
                    "precio": float(p.precio),
                })
            else:
                # Producto borrado: eliminar del carrito
                normalized.pop(pid, None)

    return normalized


def _cart_items(cart: dict):
    """
    Recibe SIEMPRE un carrito normalizado (dict de dicts).
    Devuelve (items, total) para usar en plantillas y checkout.
    """
    items = []
    total = Decimal("0.00")

    for pid, data in cart.items():
        if not isinstance(data, dict):
            continue

        try:
            cantidad = int(data.get("cantidad", 1))
        except Exception:
            cantidad = 1

        precio = Decimal(str(data.get("precio", "0")))
        nombre = data.get("nombre", f"Producto {pid}")
        subtotal = cantidad * precio
        total += subtotal

        items.append({
            "id": int(pid),     # ojo: para promos será un número grande (1_000_000 + promo_id)
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "subtotal": subtotal,
        })

    return items, total


# =========================
# VISTAS PÚBLICAS
# =========================
def index(request: HttpRequest) -> HttpResponse:
    """
    Home: últimos productos y promociones activas.
    """
    productos = Producto.objects.filter(activo=True).order_by("-id")[:12]
    promos = Promocion.objects.filter(activa=True).order_by("-id")[:8]
    categorias = Categoria.objects.filter(activa=True).order_by("nombre")

    return render(request, "index.html", {
        "productos": productos,
        "promos": promos,
        "categorias": categorias,
    })


def menu(request: HttpRequest) -> HttpResponse:
    """
    Menú agrupado por categorías activas.
    """
    categorias = (
        Categoria.objects
        .filter(activa=True)
        .prefetch_related(
            Prefetch(
                "productos",
                queryset=Producto.objects.filter(activo=True).order_by("nombre")
            )
        )
        .order_by("nombre")
    )
    return render(request, "menu.html", {"categorias": categorias})


def promociones(request: HttpRequest) -> HttpResponse:
    """
    Lista de promociones activas.
    """
    promos = Promocion.objects.filter(activa=True).order_by("-id")
    return render(request, "promociones.html", {"promos": promos})


# =========================
# CARRITO
# =========================
def carrito(request: HttpRequest) -> HttpResponse:
    """
    Muestra el carrito usando los datos de sesión.
    """
    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)
    _save_cart(request, cart)
    items, total = _cart_items(cart)
    return render(request, "carrito.html", {"items": items, "total": total})


def agregar_carrito(request: HttpRequest, producto_id: int) -> HttpResponse:
    """
    Agrega 1 unidad de un producto al carrito (por id de Producto).
    """
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)

    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)

    pid = str(producto.id)

    if pid not in cart:
        cart[pid] = {
            "nombre": producto.nombre,
            "precio": float(producto.precio),
            "cantidad": 1,
        }
    else:
        cant_actual = int(cart[pid].get("cantidad", 1))
        cart[pid]["cantidad"] = cant_actual + 1
        cart[pid]["nombre"] = producto.nombre
        cart[pid]["precio"] = float(producto.precio)

    _save_cart(request, cart)
    return redirect("carrito")


def agregar_promo_carrito(request: HttpRequest, promo_id: int) -> HttpResponse:
    """
    Agrega 1 unidad de una promoción al carrito.
    Se usa un id "grande" para no chocar con ids de productos.
    """
    promo = get_object_or_404(Promocion, pk=promo_id, activa=True)

    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)

    # Usamos un ID "grande" para no chocar con los productos normales:
    # 1_000_000 + id_promocion
    pid_num = 1_000_000 + promo.id
    pid = str(pid_num)

    if pid not in cart:
        cart[pid] = {
            "nombre": f"Promo: {promo.nombre}",
            "precio": float(promo.precio),
            "cantidad": 1,
        }
    else:
        cant_actual = int(cart[pid].get("cantidad", 1))
        cart[pid]["cantidad"] = cant_actual + 1
        cart[pid]["nombre"] = f"Promo: {promo.nombre}"
        cart[pid]["precio"] = float(promo.precio)

    _save_cart(request, cart)
    return redirect("carrito")


def eliminar_carrito(request: HttpRequest, producto_id: int) -> HttpResponse:
    """
    Elimina un ítem del carrito (producto o promo), según el id que llega desde la plantilla.
    """
    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)
    pid = str(producto_id)

    if pid in cart:
        del cart[pid]

    _save_cart(request, cart)
    return redirect("carrito")


# =========================
# CHECKOUT / ORDENES (WhatsApp)
# =========================
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Página de checkout:
    - Muestra el resumen del carrito
    - Toma los datos del cliente
    - Crea Pedido y Detalles en módulo caja
    - Envía mensaje a WhatsApp al local con el detalle del pedido
    """

    # 1) Leer carrito desde sesión
    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)
    _save_cart(request, cart)
    items, total = _cart_items(cart)

    # 2) GET -> mostrar la página de checkout
    if request.method != "POST":
        return render(request, "checkout.html", {
            "items": items,
            "total": total,
            # Si tu template tenía mp_init_point, lo dejamos como None para no romper nada
            "mp_init_point": None,
        })

    # 3) POST -> procesar el pedido
    if not items:
        # Sin carrito no hay pedido
        return redirect("carrito")

    nombre = request.POST.get("nombre", "").strip()
    email = request.POST.get("email", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    tipo_entrega = request.POST.get("tipo_entrega", "retiro")
    direccion = request.POST.get("direccion", "").strip()

    # 3.1) Crear Pedido en módulo caja
    # Usamos los mismos campos mínimos que tu success original
    pedido = Pedido.objects.create(
        origen="web",
        canal="web",
        estado="pendiente",
        nombre_cliente=nombre,
        visible_en_cocina=True,
    )

    # 3.2) Crear Detalles de Pedido (solo para productos reales)
    for it in items:
        pid = it["id"]
        # Ignoramos promos, porque usan id grandes (1_000_000 + id_promo)
        if pid >= 1_000_000:
            continue

        try:
            producto = Producto.objects.get(pk=pid)
        except Producto.DoesNotExist:
            continue

        cantidad = int(it["cantidad"])
        precio = Decimal(str(it["precio"]))

        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=precio * cantidad,
        )

    # 3.3) Construir mensaje de WhatsApp para el local
    lineas = []
    lineas.append(f"🧾 Nuevo pedido #{pedido.id}")
    lineas.append(f"Cliente: {nombre}")
    if email:
        lineas.append(f"Email: {email}")
    if telefono:
        lineas.append(f"Teléfono: {telefono}")
    lineas.append("")

    lineas.append("Detalle:")
    for it in items:
        subtotal_int = int(it["subtotal"])
        linea = f"- {it['nombre']} x{it['cantidad']} = ${subtotal_int:,}".replace(",", ".")
        lineas.append(linea)

    lineas.append("")
    total_int = int(total)
    lineas.append(f"Total: ${total_int:,}".replace(",", "."))
    lineas.append(f"Método de entrega: {tipo_entrega.capitalize()}")
    if tipo_entrega == "delivery" and direccion:
        lineas.append(f"Dirección: {direccion}")

    mensaje = "\n".join(lineas)

    numero_whatsapp = getattr(settings, "WHATSAPP_NUMERO", "")
    wa_url = None
    if numero_whatsapp:
        wa_url = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje)}"

    # 3.4) Vaciar carrito
    request.session.pop("cart", None)
    request.session.modified = True

    # 3.5) Redirigir a WhatsApp si está configurado
    if wa_url:
        return HttpResponseRedirect(wa_url)

    # Si no hay número de WhatsApp, al menos mostramos página de éxito
    return redirect("success")


# =========================
# Páginas de resultado (opcionales)
# =========================
def success(request: HttpRequest) -> HttpResponse:
    """
    Página cuando el pedido se procesa correctamente.
    (El Pedido ya se crea en checkout; aquí solo mostramos mensaje.)
    """
    return render(request, "success.html")


def failure(request: HttpRequest) -> HttpResponse:
    """
    Página cuando el pago/pedido falla (si quieres usarla).
    """
    return render(request, "failure.html")


def pending(request: HttpRequest) -> HttpResponse:
    """
    Página cuando el pago queda pendiente (si quieres usarla).
    """
    return render(request, "pending.html")
