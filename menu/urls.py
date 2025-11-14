from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("menu/", views.menu, name="menu"),
    path("promociones/", views.promociones, name="promociones"),
    path("carrito/", views.carrito, name="carrito"),

    # Productos
    path("carrito/agregar/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),

    # Promociones
    path("carrito/agregar-promo/<int:promo_id>/", views.agregar_promo_carrito, name="agregar_promo_carrito"),

    path("carrito/eliminar/<int:producto_id>/", views.eliminar_carrito, name="eliminar_carrito"),
    path("checkout/", views.checkout, name="checkout"),
    path("ordenes/success/", views.success, name="success"),
    path("ordenes/failure/", views.failure, name="failure"),
    path("ordenes/pending/", views.pending, name="pending"),
]


