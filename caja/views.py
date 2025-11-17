from decimal import Decimal
import csv
import json
from datetime import timedelta

from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import (
    Pedido,
    Boleta,
    MovimientoInventario,
    ProductoInventario,
)

# ============================================================
# PANTALLA TV COCINA (SOLO LECTURA)
# ============================================================

def cocina_tv(request):
    """
    Pantalla especial para el televisor de cocina.
    Solo muestra pedidos visibles y NO listos.
    """
    pedidos_tv = Pedido.objects.filter(
        visible_en_cocina=True,
        estado__in=["pendiente", "en_cocina"],
    ).order_by("creado_en")

    contexto = {
        "pedidos_tv": pedidos_tv,
    }
    return render(request, "caja/cocina_tv.html", contexto)


# ============================================================
# PANEL DE COCINA (PC)
# ============================================================

@login_required
def cocina_panel(request):
    """
    Panel de cocina en el PC.
    Desde aquí se toman pedidos y se marcan como listos.
    """
    pedidos_nuevos = Pedido.objects.filter(
        visible_en_cocina=True,
        estado="pendiente",
    ).order_by("creado_en")

    pedidos_en_cocina = Pedido.objects.filter(
        visible_en_cocina=True,
        estado="en_cocina",
    ).order_by("creado_en")

    contexto = {
        "pedidos_nuevos": pedidos_nuevos,
        "pedidos_en_cocina": pedidos_en_cocina,
    }
    return render(request, "caja/cocina_panel.html", contexto)


@login_required
def cocina_cambiar_estado(request, pedido_id, nuevo_estado):
    """
    Cambia el estado de un pedido desde el panel de cocina.
    - pendiente   -> sigue visible en TV
    - en_cocina   -> sigue visible en TV
    - listo       -> se oculta de TV y del panel
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if nuevo_estado == "pendiente":
        pedido.estado = "pendiente"
        pedido.visible_en_cocina = True

    elif nuevo_estado == "en_cocina":
        pedido.estado = "en_cocina"
        pedido.visible_en_cocina = True

    elif nuevo_estado == "listo":
        pedido.estado = "listo"
        pedido.visible_en_cocina = False

    pedido.save()
    return redirect("cocina_panel")


# ============================================================
# PANEL DE CAJA (PRESENCIAL)
# ============================================================

@login_required
def caja_panel(request):
    """
    Panel principal de Caja.
    - Crea un Pedido de origen local.
    - Genera automáticamente la Boleta asociada para que aparezca en reportes.
    """
    ahora = timezone.localtime()

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        forma_pago = request.POST.get("forma_pago", "")
        tipo_entrega = request.POST.get("tipo_entrega", "")
        detalle = request.POST.get("detalle", "").strip()
        total_str = request.POST.get("total", "0").strip()

        # Parseamos el total manual (lo que escribe el cajero)
        try:
            total_manual = Decimal(total_str)
        except Exception:
            total_manual = Decimal("0")

        # 1) Creamos el Pedido
        pedido = Pedido.objects.create(
            nombre_cliente=nombre,
            telefono=telefono,
            direccion=direccion,
            forma_pago=forma_pago,
            tipo_entrega=tipo_entrega,
            nota=detalle,          # descripción general de la comanda
            origen="local",
            canal="mostrador",
            visible_en_cocina=True,
            estado="pendiente",
            total_manual=total_manual,
        )

        # 2) Creamos la Boleta asociada (para reportes y dashboard)
        Boleta.objects.create(
            pedido=pedido,
            folio=Boleta.siguiente_folio(),
            monto_total=pedido.total,        # usa total_manual si no hay detalles
            metodo_pago=forma_pago or "efectivo",
        )

        # 3) Volvemos a la misma pantalla de caja
        return redirect("caja_panel")

    contexto = {
        "dia": ahora.strftime("%d"),
        "mes": ahora.strftime("%m"),
        "ano": ahora.strftime("%Y"),
        "hora": ahora.strftime("%H:%M"),
    }
    return render(request, "caja/caja_panel.html", contexto)


# ============================================================
# BOLETA HTML + PDF
# ============================================================

def caja_ver_boleta(request, pedido_id):
    """
    Vista para mostrar la boleta de un pedido en HTML.
    La URL recibe el ID del pedido.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    boleta = getattr(pedido, "boleta", None)

    # Si aún no existe boleta para este pedido, creamos una simple
    # solo para evitar errores (modo demo).
    if boleta is None:
        boleta = Boleta.objects.create(
            pedido=pedido,
            folio=Boleta.siguiente_folio(),
            monto_total=pedido.total,
            metodo_pago=pedido.forma_pago or "manual",
        )

    detalles = pedido.detalles.select_related("producto").all()

    contexto = {
        "pedido": boleta,   # el template usa propiedades de Boleta como si fuera "pedido"
        "detalles": detalles,
    }
    return render(request, "caja/boleta.html", contexto)


# -------- PDF tipo boleta SII (demo) --------
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


@login_required
def boleta_pdf(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    boleta = getattr(pedido, "boleta", None)

    if boleta is None:
        boleta = Boleta.objects.create(
            pedido=pedido,
            folio=Boleta.siguiente_folio(),
            monto_total=pedido.total,
            metodo_pago=pedido.forma_pago or "manual",
        )

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Encabezado similar a boleta SII (simplificado)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, height - 50, "QUINCHO VIDELA")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 65, "RUT: 11.111.111-1")
    p.drawString(40, height - 80, "Giro: Restaurante y Minimarket")
    p.drawString(40, height - 95, "Dirección: Punta Arenas")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(width - 200, height - 50, "BOLETA ELECTRÓNICA")
    p.drawString(width - 200, height - 65, f"Folio: {boleta.folio}")

    # Datos básicos
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 130, f"Fecha: {boleta.fecha_emision.strftime('%d-%m-%Y %H:%M')}")
    p.drawString(40, height - 145, f"Cliente: {pedido.nombre_cliente or 'Venta mostrador'}")

    # Detalle
    y = height - 180
    p.drawString(40, y, "Cant.")
    p.drawString(90, y, "Descripción")
    p.drawString(width - 150, y, "P.U.")
    p.drawString(width - 80, y, "Total")
    y -= 15

    for det in pedido.detalles.all():
        p.drawString(40, y, str(det.cantidad))
        p.drawString(90, y, det.nombre_producto[:30])
        p.drawRightString(width - 90, y, f"{det.precio_unitario:,.0f}")
        p.drawRightString(width - 20, y, f"{det.subtotal:,.0f}")
        y -= 15
        if y < 80:  # nueva página si se acaba el espacio
            p.showPage()
            y = height - 80

    # Totales
    y -= 20
    p.drawRightString(width - 20, y, f"TOTAL: {pedido.total:,.0f}")

    # Pie
    y -= 40
    p.setFont("Helvetica", 8)
    p.drawString(40, y, "Timbre electrónico SII (demo)")
    p.drawString(40, y - 12, "Documento no válido como boleta electrónica real ante el SII.")

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="boleta_{boleta.folio}.pdf"'
    response.write(pdf)
    return response


# ============================================================
# DASHBOARD FINANCIERO / INVENTARIO (inventario_lista.html)
# ============================================================
@login_required
def inventario_panel(request):
    """
    Dashboard general (ventas + inventario + gráficos + tablas),
    todo en una sola página: caja/inventario_lista.html.
    """

    hoy = timezone.localdate()
    ahora = timezone.localtime()
    primer_dia_mes = hoy.replace(day=1)

    # -------- VENTAS: HOY --------
    boletas_hoy = (
        Boleta.objects.select_related("pedido")
        .filter(fecha_emision__date=hoy)
        .order_by("-fecha_emision")
    )
    total_boletas_hoy = boletas_hoy.count()
    total_venta_hoy = boletas_hoy.aggregate(suma=Sum("monto_total"))["suma"] or Decimal("0")
    ticket_promedio_hoy = (
        (total_venta_hoy / total_boletas_hoy) if total_boletas_hoy > 0 else Decimal("0")
    )

    # -------- VENTAS: MES --------
    boletas_mes = (
        Boleta.objects.select_related("pedido")
        .filter(
            fecha_emision__date__gte=primer_dia_mes,
            fecha_emision__date__lte=hoy,
        )
    )
    total_boletas_mes = boletas_mes.count()
    total_venta_mes = boletas_mes.aggregate(suma=Sum("monto_total"))["suma"] or Decimal("0")
    ticket_promedio_mes = (
        (total_venta_mes / total_boletas_mes) if total_boletas_mes > 0 else Decimal("0")
    )

    # -------- INVENTARIO --------
    total_productos = ProductoInventario.objects.count()

    valor_expr = ExpressionWrapper(
        F("stock_actual") * F("precio_costo"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    valor_inventario = (
        ProductoInventario.objects.annotate(valor=valor_expr)
        .aggregate(suma=Sum("valor"))["suma"]
        or Decimal("0")
    )

    productos_criticos = (
        ProductoInventario.objects.filter(stock_actual__lte=10)
        .order_by("stock_actual", "nombre")
    )

    # -------- GRÁFICO: VENTAS ÚLTIMOS 7 DÍAS --------
    dias_atras = 6
    desde_7 = hoy - timedelta(days=dias_atras)

    boletas_ultimos = (
        Boleta.objects.filter(fecha_emision__date__gte=desde_7, fecha_emision__date__lte=hoy)
        .values("fecha_emision__date")
        .annotate(total_dia=Sum("monto_total"))
        .order_by("fecha_emision__date")
    )

    ventas_dict = {b["fecha_emision__date"]: b["total_dia"] for b in boletas_ultimos}

    ventas_labels = []
    ventas_data = []
    for i in range(dias_atras, -1, -1):
        dia = hoy - timedelta(days=i)
        label = dia.strftime("%d-%m")
        ventas_labels.append(label)
        ventas_data.append(float(ventas_dict.get(dia, 0) or 0))

    # -------- GRÁFICO: MOVIMIENTOS INVENTARIO (ENTRADAS / SALIDAS) --------
    movs_qs = (
        MovimientoInventario.objects
        .filter(fecha__date__gte=desde_7, fecha__date__lte=hoy)
        .values("fecha__date", "tipo")
        .annotate(total=Sum("cantidad"))
        .order_by("fecha__date", "tipo")
    )

    mov_dict = {}
    for fila in movs_qs:
        f = fila["fecha__date"]
        if f not in mov_dict:
            mov_dict[f] = {"entrada": 0, "salida": 0}
        mov_dict[f][fila["tipo"]] = fila["total"]

    mov_labels = []
    mov_entradas = []
    mov_salidas = []
    for i in range(dias_atras, -1, -1):
        dia = hoy - timedelta(days=i)
        label = dia.strftime("%d-%m")
        mov_labels.append(label)
        valores = mov_dict.get(dia, {"entrada": 0, "salida": 0})
        mov_entradas.append(int(valores["entrada"] or 0))
        mov_salidas.append(int(valores["salida"] or 0))

    # -------- TABLAS EXTRA PARA EL MISMO DASHBOARD --------
    # Historial reciente de ventas (últimas 50 boletas)
    ventas_recientes = (
        Boleta.objects.select_related("pedido")
        .order_by("-fecha_emision")[:50]
    )

    # Movimientos de inventario recientes (últimos 100)
    movimientos_recientes = (
        MovimientoInventario.objects
        .select_related("producto")
        .order_by("-fecha")[:100]
    )

    contexto = {
        # Ventas hoy
        "total_boletas_hoy": total_boletas_hoy,
        "total_venta_hoy": total_venta_hoy,
        "ticket_promedio_hoy": ticket_promedio_hoy,
        "boletas_hoy": boletas_hoy,

        # Ventas mes
        "total_boletas_mes": total_boletas_mes,
        "total_venta_mes": total_venta_mes,
        "ticket_promedio_mes": ticket_promedio_mes,

        # Inventario
        "total_productos": total_productos,
        "valor_inventario": valor_inventario,
        "productos_criticos": productos_criticos,

        # Gráfico ventas
        "ventas_labels": json.dumps(ventas_labels),
        "ventas_data": json.dumps(ventas_data),

        # Gráfico movimientos inventario
        "mov_labels": json.dumps(mov_labels),
        "mov_entradas": json.dumps(mov_entradas),
        "mov_salidas": json.dumps(mov_salidas),

        # Tablas en el mismo dashboard
        "ventas_recientes": ventas_recientes,
        "movimientos_recientes": movimientos_recientes,
    }
    return render(request, "caja/inventario_lista.html", contexto)


@login_required
def inventario_movimiento(request):
    """
    Lista de movimientos de inventario (entradas/salidas).
    """
    movimientos = (
        MovimientoInventario.objects.select_related("producto")
        .order_by("-fecha")[:200]
    )

    contexto = {
        "movimientos": movimientos,
    }
    return render(request, "caja/inventario_movimiento.html", contexto)


# ============================================================
# GRÁFICO DE MOVIMIENTOS (PÁGINA SEPARADA)
# ============================================================

@login_required
def reporte_movimientos(request):
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=6)

    qs = (
        MovimientoInventario.objects
        .filter(fecha__date__gte=desde, fecha__date__lte=hoy)
        .values("fecha__date", "tipo")  # tipo = "entrada"/"salida"
        .annotate(total=Sum("cantidad"))
        .order_by("fecha__date", "tipo")
    )

    datos_por_dia = {}
    for fila in qs:
        f = fila["fecha__date"].strftime("%d-%m")
        if f not in datos_por_dia:
            datos_por_dia[f] = {"entrada": 0, "salida": 0}
        datos_por_dia[f][fila["tipo"]] = fila["total"]

    labels = []
    entradas = []
    salidas = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        clave = dia.strftime("%d-%m")
        labels.append(clave)
        valores = datos_por_dia.get(clave, {"entrada": 0, "salida": 0})
        entradas.append(valores["entrada"] or 0)
        salidas.append(valores["salida"] or 0)

    contexto = {
        "labels": json.dumps(labels),
        "entradas": json.dumps(entradas),
        "salidas": json.dumps(salidas),
    }
    return render(request, "caja/reporte_movimientos.html", contexto)


# ============================================================
# REPORTE HISTÓRICO DE VENTAS (reporte.html)
# ============================================================

@login_required
def reporte_ventas(request):
    """
    Reporte histórico de ventas con filtros.
    Usa el template: caja/reporte.html
    """
    qs = Pedido.objects.select_related("boleta").filter(boleta__isnull=False)

    # Filtros GET
    f_desde = request.GET.get("desde") or ""
    f_hasta = request.GET.get("hasta") or ""
    f_cliente = request.GET.get("cliente") or ""
    f_producto = request.GET.get("producto") or ""
    f_dia = request.GET.get("dia") or ""
    f_mes = request.GET.get("mes") or ""
    f_anio = request.GET.get("anio") or ""

    # Filtrar por rango de fechas (boleta)
    if f_desde:
        qs = qs.filter(boleta__fecha_emision__date__gte=f_desde)
    if f_hasta:
        qs = qs.filter(boleta__fecha_emision__date__lte=f_hasta)

    # Filtrar por día/mes/año específico (si se usan)
    if f_dia:
        qs = qs.filter(boleta__fecha_emision__day=f_dia)
    if f_mes:
        qs = qs.filter(boleta__fecha_emision__month=f_mes)
    if f_anio:
        qs = qs.filter(boleta__fecha_emision__year=f_anio)

    # Cliente
    if f_cliente:
        qs = qs.filter(nombre_cliente__icontains=f_cliente)

    # Producto (buscamos en detalle nombre_producto)
    if f_producto:
        qs = qs.filter(detalles__nombre_producto__icontains=f_producto).distinct()

    qs = qs.order_by("-boleta__fecha_emision")

    total_boletas = qs.count()
    total_general = (
        qs.aggregate(suma=Sum("boleta__monto_total"))["suma"] or Decimal("0")
    )
    ticket_promedio = (
        (total_general / total_boletas) if total_boletas > 0 else Decimal("0")
    )

    contexto = {
        "pedidos": qs,
        "total_boletas": total_boletas,
        "total_general": total_general,
        "ticket_promedio": ticket_promedio,

        # Filtros para mantener en el formulario
        "f_desde": f_desde,
        "f_hasta": f_hasta,
        "f_cliente": f_cliente,
        "f_producto": f_producto,
        "f_dia": f_dia,
        "f_mes": f_mes,
        "f_anio": f_anio,
    }
    return render(request, "caja/reporte.html", contexto)


# ============================================================
# EXPORTACIONES A "EXCEL" (CSV)
# ============================================================

@login_required
def exportar_ventas_excel(request):
    """
    Exporta las ventas (boletas) a CSV, abrible en Excel.
    Opcionalmente respeta los mismos filtros usados en reporte_ventas.
    """
    qs = Pedido.objects.select_related("boleta").filter(boleta__isnull=False)

    f_desde = request.GET.get("desde") or ""
    f_hasta = request.GET.get("hasta") or ""
    f_cliente = request.GET.get("cliente") or ""
    f_producto = request.GET.get("producto") or ""
    f_dia = request.GET.get("dia") or ""
    f_mes = request.GET.get("mes") or ""
    f_anio = request.GET.get("anio") or ""

    if f_desde:
        qs = qs.filter(boleta__fecha_emision__date__gte=f_desde)
    if f_hasta:
        qs = qs.filter(boleta__fecha_emision__date__lte=f_hasta)
    if f_dia:
        qs = qs.filter(boleta__fecha_emision__day=f_dia)
    if f_mes:
        qs = qs.filter(boleta__fecha_emision__month=f_mes)
    if f_anio:
        qs = qs.filter(boleta__fecha_emision__year=f_anio)
    if f_cliente:
        qs = qs.filter(nombre_cliente__icontains=f_cliente)
    if f_producto:
        qs = qs.filter(detalles__nombre_producto__icontains=f_producto).distinct()

    qs = qs.order_by("-boleta__fecha_emision")

    response = HttpResponse(content_type="text/csv")
    filename = "ventas_quincho_videla.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "Folio",
        "Fecha emision",
        "Cliente",
        "Origen",
        "Forma pago",
        "Total",
    ])

    for p in qs:
        boleta = p.boleta
        writer.writerow([
            boleta.folio,
            boleta.fecha_emision.strftime("%Y-%m-%d %H:%M"),
            p.nombre_cliente or "",
            p.get_origen_display(),
            p.forma_pago or "",
            f"{boleta.monto_total:.0f}",
        ])

    return response


@login_required
def exportar_inventario_excel(request):
    """
    Exporta el inventario (ProductoInventario) a CSV, abrible en Excel.
    """
    productos = ProductoInventario.objects.all().order_by("nombre")

    response = HttpResponse(content_type="text/csv")
    filename = "inventario_quincho_videla.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "SKU",
        "Nombre",
        "Stock actual",
        "Precio costo",
        "Precio venta",
        "Valor total (costo)",
    ])

    for prod in productos:
        valor_total = (prod.stock_actual or 0) * (prod.precio_costo or 0)
        writer.writerow([
            prod.sku or "",
            prod.nombre,
            prod.stock_actual,
            f"{prod.precio_costo:.0f}",
            f"{prod.precio_venta:.0f}",
            f"{valor_total:.0f}",
        ])

    return response
