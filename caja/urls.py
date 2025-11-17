from django.urls import path
from . import views

app_name = "caja"

urlpatterns = [
    # 👉 Ruta raíz del módulo caja: será /caja/ en la web
    path("", views.caja_panel, name="caja_panel"),

    path("cocina/", views.cocina_panel, name="cocina_panel"),
    path("cocina/tv/", views.cocina_tv, name="cocina_tv"),
    path("cocina/<int:pedido_id>/<str:nuevo_estado>/", views.cocina_cambiar_estado, name="cocina_cambiar_estado"),
    path("inventario/", views.inventario_panel, name="inventario_panel"),
    path("inventario/movimientos/", views.inventario_movimiento, name="inventario_movimiento"),
    path("reportes/movimientos/", views.reporte_movimientos, name="reporte_movimientos"),
    path("reportes/ventas/", views.reporte_ventas, name="reporte_ventas"),
    path("boleta/<int:pedido_id>/", views.caja_ver_boleta, name="caja_ver_boleta"),
    path("boleta/<int:pedido_id>/pdf/", views.boleta_pdf, name="boleta_pdf"),
    path("exportar/ventas/", views.exportar_ventas_excel, name="exportar_ventas_excel"),
    path("exportar/inventario/", views.exportar_inventario_excel, name="exportar_inventario_excel"),
]
