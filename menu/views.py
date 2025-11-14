# menu/views.py
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.db.models import Prefetch

from .models import Producto, Promocion, Categoria


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
            "id": int(pid),     # ojo: para promos será un número grande
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
        "productos": productos,    # lista de productos
        "promos": promos,          # promos para el {% for p in promos %}
        "categorias": categorias,  # categorías para el bloque de categorías
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

    # Usamos un ID "grande" para no chocar con los productos normales
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
# CHECKOUT / ORDENES
# =========================
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Página de checkout.
    Si MercadoPago está configurado (MP_ACCESS_TOKEN), crea preferencia.
    Si no, muestra el resumen del carrito sin fallar.
    """
    cart = _get_cart(request)
    cart = _normalize_cart_dict(cart)
    _save_cart(request, cart)
    items, total = _cart_items(cart)

    mp_token = getattr(settings, "MP_ACCESS_TOKEN", None)
    init_point = None

    if mp_token:
        try:
            from mercadopago import SDK
            sdk = SDK(mp_token)

            mp_items = []
            for it in items:
                mp_items.append({
                    "title": it["nombre"],
                    "quantity": int(it["cantidad"]),
                    "unit_price": float(it["precio"]),
                    "currency_id": "CLP",
                })

            base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
            preference_data = {
                "items": mp_items,
                "back_urls": {
                    "success": f"{base_url}{reverse('success')}",
                    "failure": f"{base_url}{reverse('failure')}",
                    "pending": f"{base_url}{reverse('pending')}",
                },
                "auto_return": "approved",
            }
            preference = sdk.preference().create(preference_data)
            init_point = (
                preference["response"].get("init_point")
                or preference["response"].get("sandbox_init_point")
            )
        except Exception:
            # No reventar la vista si falla MP
            init_point = None

    return render(request, "checkout.html", {
        "items": items,
        "total": total,
        "mp_init_point": init_point,
    })


def success(request: HttpRequest) -> HttpResponse:
    """
    Página de éxito de pago.
    Si quieres vaciar el carrito al terminar, descomenta las 2 líneas.
    """
    # request.session.pop("cart", None)
    # request.session.modified = True
    return render(request, "success.html")


def failure(request: HttpRequest) -> HttpResponse:
    """
    Página cuando el pago falla.
    """
    return render(request, "failure.html")


def pending(request: HttpRequest) -> HttpResponse:
    """
    Página cuando el pago queda pendiente.
    """
    return render(request, "pending.html")
